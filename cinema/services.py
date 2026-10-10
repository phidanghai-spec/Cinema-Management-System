"""
Cinema Service Layer - Business Logic (Service Pattern).

This module contains all business rules and workflow orchestration,
delegating data access to the Repository layer and design pattern
execution to the Patterns module.
"""

import logging
import datetime
import json
import re
import urllib.request
import urllib.error
from typing import Optional, List, Tuple
from django.db import transaction
from django.conf import settings

from .models import (
    User, Movie, Theater, Screen, Seat,
    Showtime, Booking, BookingItem, Payment,
    Review, Discount, Favorite, Watchlist,
    Address, InAppNotification
)
from .repositories import (
    UserRepository, MovieRepository, BookingRepository,
    ShowtimeRepository, DiscountRepository
)
from .patterns import (
    StandardBookingWorkflow, get_booking_state_class,
    PaymentProcessorFactory, get_discount_validation_chain
)

logger = logging.getLogger(__name__)


from .exceptions import (
    CinemaException,
    UserNotFoundException,
    DuplicateEmailException,
    AccountBannedException,
    InvalidCredentialsException,
    MovieNotFoundException,
    ShowtimeNotFoundException,
    SeatNotFoundException,
    BookingNotFoundException,
    UnauthorizedActionException,
    InvalidTicketException,
    SeatAlreadyBookedException,
    InsufficientPointsException,
    DiscountNotApplicableException,
    PaymentTimeoutException,
    InvalidStateTransitionException
)


# ── UserService ───────────────────────────────────────────────────────────────

class UserService:
    """Business logic for user registration and authentication."""

    @staticmethod
    def register(email: str, password: str, name: str, phone: Optional[str] = None) -> User:
        """
        Register a new customer account.

        Validates that the email is unique, then delegates creation
        to UserRepository which hashes the password before storing.

        Args:
            email:    Unique email address for the new account.
            password: Plain-text password (will be hashed via bcrypt).
            name:     Full display name shown in the UI.
            phone:    Optional mobile phone number.

        Returns:
            The newly created and active User instance.

        Raises:
            DuplicateEmailException: If another account already uses this email.

        Example:
            >>> user = UserService.register('new@example.com', 'pass123', 'Nguyen A')
            >>> print(user.tier)
            'Bronze'
        """
        logger.info(f"Attempting registration for email={email}")
        if UserRepository.get_by_email(email):
            raise DuplicateEmailException("Email already registered.")
        user = UserRepository.create_user(email, password, name, phone)
        logger.info(f"Registration successful for user id={user.id}")
        return user

    @staticmethod
    def login(email: str, password: str) -> User:
        """
        Authenticate a user with email and password.

        Args:
            email:    The account email address.
            password: Plain-text password to verify against stored hash.

        Returns:
            The authenticated User instance on success.

        Raises:
            InvalidCredentialsException: If email not found or password is wrong.
            AccountBannedException:      If the account has been banned by admin.

        Example:
            >>> user = UserService.login('admin@cinema.com', 'admin123')
            >>> print(user.name)
            'Admin User'
        """
        logger.info(f"Login attempt for email={email}")
        user = UserRepository.get_by_email(email)
        if not user:
            raise InvalidCredentialsException("Invalid email or password.")
        if user.status == 'banned':
            logger.warning(f"Banned user login attempt: email={email}")
            raise AccountBannedException("Account has been banned.")
        if not user.check_password(password):
            logger.warning(f"Wrong password for email={email}")
            raise InvalidCredentialsException("Invalid email or password.")
        logger.info(f"Login successful for user id={user.id}")
        return user


# ── MovieService ──────────────────────────────────────────────────────────────

class MovieService:
    """Business logic for movie catalog browsing and discovery."""

    @staticmethod
    def get_movies(
        status: Optional[str] = None,
        genre: Optional[str] = None,
        format_type: Optional[str] = None,
        search: Optional[str] = None,
        sort: Optional[str] = None
    ):
        """
        Return a filtered and sorted list of movies.

        Delegates to MovieRepository with the supplied filter criteria.

        Args:
            status:      Status filter slug (e.g. 'now_showing', 'coming_soon').
            genre:       Genre keyword for partial match (e.g. 'Action').
            format_type: Format filter (e.g. '2D', '3D', 'IMAX').
            search:      Free-text search on title and description.
            sort:        Sort key: 'rating', 'newest', or 'title'.

        Returns:
            QuerySet of matching Movie objects.
        """
        return MovieRepository.filter_movies(status, genre, format_type, search, sort)

    @staticmethod
    def get_details(movie_id: int) -> Movie:
        """
        Retrieve full details for a single movie.

        Args:
            movie_id: The primary key of the movie to retrieve.

        Returns:
            The Movie instance with all fields.

        Raises:
            MovieNotFoundException: If no movie exists with the given ID.
        """
        movie = MovieRepository.get_by_id(movie_id)
        if not movie:
            raise MovieNotFoundException(f"Movie with id={movie_id} not found.")
        return movie


# ── TheaterService ────────────────────────────────────────────────────────────

class TheaterService:
    """Business logic for theater and screen management."""

    @staticmethod
    @transaction.atomic
    def create_screen(
        theater_id: int,
        name: str,
        format_type: str,
        rows: int,
        columns: int
    ) -> Screen:
        """
        Create a new cinema screen and auto-generate its seat layout.

        Seats are assigned types by row position:
        - First 3 rows → Normal (80,000 VND)
        - Middle rows  → VIP (120,000 VND)
        - Last row     → Couple (200,000 VND, paired seats)

        Args:
            theater_id:  ID of the parent Theater.
            name:        Display name of the screen (e.g. 'Screen 1').
            format_type: Projection format ('2D', '3D', 'IMAX').
            rows:        Number of seat rows to generate.
            columns:     Number of seats per row.

        Returns:
            The newly created Screen with all seats generated.

        Raises:
            Theater.DoesNotExist: If theater_id references a non-existent theater.

        Note:
            Couple seats occupy two adjacent column slots and are wider in the UI.
        """
        logger.info(f"Creating screen '{name}' for theater id={theater_id}")
        theater = Theater.objects.get(id=theater_id)
        capacity = rows * columns
        screen = Screen.objects.create(
            theater=theater,
            name=name,
            format=format_type,
            capacity=capacity,
            rows=rows,
            columns=columns
        )

        for r_idx in range(rows):
            row_char = chr(65 + r_idx)  # A, B, C...
            is_couple_row = (r_idx == rows - 1)

            if is_couple_row:
                for col_idx in range(1, columns + 1, 2):
                    seat_num = (
                        f"{row_char}{col_idx}-{col_idx + 1}"
                        if col_idx + 1 <= columns
                        else f"{row_char}{col_idx}"
                    )
                    Seat.objects.create(
                        screen=screen, row=row_char, column=col_idx,
                        seat_number=seat_num, type='couple',
                        price=200000, status='available'
                    )
            else:
                for col_idx in range(1, columns + 1):
                    seat_type = 'normal' if r_idx < 3 else 'vip'
                    price = 80000 if seat_type == 'normal' else 120000
                    Seat.objects.create(
                        screen=screen, row=row_char, column=col_idx,
                        seat_number=f"{row_char}{col_idx}",
                        type=seat_type, price=price, status='available'
                    )

        logger.info(f"Screen id={screen.id} created with {capacity} seats")
        return screen


# ── BookingService ────────────────────────────────────────────────────────────

class BookingService:
    """Business logic for the full ticket booking and cancellation lifecycle."""

    @staticmethod
    @transaction.atomic
    def make_booking(
        user_id: int,
        showtime_id: int,
        seat_ids: List[int],
        combo_items: Optional[List[dict]] = None,
        discount_code: Optional[str] = None,
        method: str = "credit_card",
        phone: str = "",
        notes: str = "",
        redeemed_points: int = 0
    ) -> Booking:
        """
        Execute the full booking workflow for a user.

        Validates all inputs, then delegates to StandardBookingWorkflow
        which internally applies Strategy (pricing), Builder (construction),
        Chain of Responsibility (discount), Adapter (payment), and
        Observer (notifications) patterns.

        Args:
            user_id:       ID of the authenticated user making the booking.
            showtime_id:   ID of the selected showtime.
            seat_ids:      List of seat IDs the user has chosen.
            combo_items:   Optional list of food and drink combos.
            discount_code: Optional coupon code string (e.g. 'SUMMER2026').
            method:        Payment method slug: 'credit_card' or 'momo'.
            phone:         Phone number for MoMo payments.
            notes:         Optional special requests from the user.
            redeemed_points: Loyalty points redeemed for cash discount.

        Returns:
            The confirmed Booking instance with payment completed.

        Raises:
            UserNotFoundException:     If user_id does not exist.
            ShowtimeNotFoundException: If showtime_id does not exist.
            SeatNotFoundException:     If any seat_id is not found.
            CinemaException:           If business rules are violated
                                       (e.g. seat unavailable, discount expired).

        Example:
            >>> booking = BookingService.make_booking(
            ...     user_id=1, showtime_id=3,
            ...     seat_ids=[10, 11], discount_code='SUMMER2026'
            ... )
            >>> print(booking.status)
            'confirmed'
        """
        logger.info(f"Starting booking: user={user_id}, showtime={showtime_id}, seats={seat_ids}, points={redeemed_points}")

        user = UserRepository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException("User not found.")

        showtime = ShowtimeRepository.get_by_id(showtime_id)
        if not showtime:
            raise ShowtimeNotFoundException("Showtime not found.")

        seats = Seat.objects.filter(id__in=seat_ids)
        if len(seats) != len(seat_ids):
            raise SeatNotFoundException("Some seats were not found.")

        workflow = StandardBookingWorkflow()
        booking, payment = workflow.execute(
            user=user,
            showtime=showtime,
            seats=seats,
            combo_items=combo_items,
            discount_code=discount_code,
            notes=notes,
            payment_method=method,
            phone=phone,
            redeemed_points=redeemed_points
        )

        logger.info(f"Booking id={booking.id} completed successfully — total={booking.total_price}")
        return booking


    @staticmethod
    @transaction.atomic
    def cleanup_expired_bookings():
        from django.utils import timezone
        from datetime import timedelta
        from .patterns import SystemSettings, get_booking_state_class
        
        settings = SystemSettings.get_instance()
        timeout_minutes = settings.seat_lock_timeout_minutes
        cutoff_time = timezone.now() - timedelta(minutes=timeout_minutes)
        
        expired_bookings = Booking.objects.filter(
            status='pending',
            created_at__lt=cutoff_time
        )
        
        for booking in expired_bookings:
            try:
                state = get_booking_state_class(booking.status)
                state.cancel(booking)
                logger.info(f"Automatically cancelled expired pending booking #{booking.id}")
            except Exception as e:
                logger.error(f"Error auto-cancelling expired booking #{booking.id}: {e}")

    @staticmethod
    @transaction.atomic
    def cancel_booking(booking_id: int, user_id: int) -> Booking:
        """
        Cancel a confirmed booking and process any applicable refund.

        Applies the State Pattern to validate the transition, calculates
        a 90% refund (10% cancellation fee via SystemSettings Singleton),
        and triggers notifications via the Observer pattern.

        Args:
            booking_id: ID of the booking to cancel.
            user_id:    ID of the user requesting cancellation (for ownership check).

        Returns:
            The cancelled Booking instance with refund_amount set.

        Raises:
            BookingNotFoundException:   If booking_id does not exist.
            UnauthorizedActionException: If the booking belongs to a different user.
            CinemaException:            If the booking is not in a cancellable state
                                        (e.g. already cancelled or completed).

        Note:
            - Refund is processed via the original payment adapter.
            - A negative-amount Payment record is created to track the refund.
            - Cancellation notifications are sent to email and in-app channels.
        """
        logger.info(f"Cancel request: booking={booking_id}, user={user_id}")

        booking = BookingRepository.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundException("Booking not found.")
        if booking.user_id != user_id:
            logger.warning(f"Unauthorized cancel: booking owner={booking.user_id}, requester={user_id}")
            raise UnauthorizedActionException("Unauthorized cancellation request.")

        state = get_booking_state_class(booking.status)
        state.cancel(booking)
        booking.payments.filter(status='pending').update(status='failed')

        if booking.refund_amount > 0:
            payment = booking.payments.filter(status='completed').first()
            if payment:
                factory = PaymentProcessorFactory()
                processor = factory.create_processor(payment.method)
                processor.refund(payment.transaction_id, booking.refund_amount)

                Payment.objects.create(
                    booking=booking,
                    amount=-booking.refund_amount,
                    method=payment.method,
                    transaction_id=f"ref_{payment.transaction_id}",
                    status='completed'
                )
                logger.info(f"Refund of {booking.refund_amount} VND processed for booking id={booking_id}")

        from .patterns import BookingSubject, EmailObserver, InAppObserver
        subject = BookingSubject()
        subject.attach(EmailObserver())
        subject.attach(InAppObserver())
        subject.notify(booking, "booking_cancelled")

        return booking

    @staticmethod
    def verify_ticket(qr_code_str: str) -> Booking:
        """
        Verify a cinema entrance QR code and mark the ticket as completed.

        Parses the QR content in the format 'CINEMA-BOOKING-ID:<int>',
        then transitions the booking state from 'confirmed' → 'completed'
        via the State Pattern.

        Args:
            qr_code_str: The raw QR code content string scanned at the entrance.

        Returns:
            The completed Booking instance.

        Raises:
            InvalidTicketException: If the QR format is invalid, the booking
                                    does not exist, or the state transition fails.

        Example:
            >>> booking = BookingService.verify_ticket('CINEMA-BOOKING-ID:42')
            >>> print(booking.status)
            'completed'
        """
        logger.info(f"Verifying ticket QR: {qr_code_str}")

        if not qr_code_str.startswith("CINEMA-BOOKING-ID:"):
            raise InvalidTicketException("Invalid ticket QR code format.")

        try:
            booking_id = int(qr_code_str.split(":")[1])
        except (IndexError, ValueError):
            raise InvalidTicketException("Malformed ticket code.")

        booking = BookingRepository.get_by_id(booking_id)
        if not booking:
            raise InvalidTicketException("Ticket booking not found.")

        state = get_booking_state_class(booking.status)
        state.complete(booking)

        logger.info(f"Ticket verified — booking id={booking_id} marked as completed")
        return booking

    @staticmethod
    @transaction.atomic
    def confirm_bank_transfer(booking_id: int, user_id: int) -> Booking:
        """
        Confirm manual or VietQR bank transfer payment for a booking.
        Transitions state from 'pending' -> 'confirmed' and sends notifications.
        """
        logger.info(f"Confirming bank transfer for booking id={booking_id} by user id={user_id}")
        booking = BookingRepository.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundException(f"Booking #{booking_id} not found.")

        # Check permission: booking owner or admin/staff
        user = UserRepository.get_by_id(user_id)
        if not user or (booking.user_id != user_id and user.role not in ['admin', 'staff']):
            raise UnauthorizedActionException("Unauthorized action on booking.")

        # Find pending payment
        payment = booking.payments.filter(status='pending').last()
        if not payment:
            payment = booking.payments.last()

        if payment:
            payment.status = 'completed'
            payment.save(update_fields=['status'])

        if booking.status == 'pending':
            state = get_booking_state_class(booking.status)
            state.confirm(booking)

            from .patterns import BookingSubject, EmailObserver, InAppObserver
            subject = BookingSubject()
            subject.attach(EmailObserver())
            subject.attach(InAppObserver())
            subject.notify(booking, "booking_confirmed")

        logger.info(f"Booking #{booking.id} bank transfer confirmed successfully.")
        return booking


# ── MovieSyncService ──────────────────────────────────────────────────────────

class MovieSyncService:
    """
    Business service to synchronize movie catalog from public APIs:
    - TMDB API (The Movie Database) with Vietnamese localization
    - TVMaze public API as open fallback (no API key required)
    - Curated cinema releases fallback for offline or zero-network reliability
    
    Prevents duplicates by utilizing Movie.objects.update_or_create.
    """

    TMDB_GENRES = {
        28: "Hành Động",
        12: "Phiêu Lưu",
        16: "Hoạt Hình",
        35: "Hài Hước",
        80: "Hình Sự",
        99: "Tài Liệu",
        18: "Chính Kịch",
        10751: "Gia Đình",
        14: "Kỳ Ảo",
        36: "Lịch Sử",
        27: "Kinh Dị",
        10402: "Âm Nhạc",
        9648: "Bí Ẩn",
        10749: "Lãng Mạn",
        878: "Khoa Học Viễn Tưởng",
        10770: "Phim Truyền Hình",
        53: "Gây Cấn",
        10752: "Chiến Tranh",
        37: "Miền Tây",
    }

    @classmethod
    def fetch_from_tmdb(cls, limit: int = 10) -> Optional[List[dict]]:
        """Fetch now playing movies from TMDB API."""
        api_key = getattr(settings, 'TMDB_API_KEY', '').strip()
        if not api_key:
            logger.info("TMDB_API_KEY is not configured, skipping direct TMDB API call.")
            return None

        url = f"https://api.themoviedb.org/3/movie/now_playing?api_key={api_key}&language=vi-VN&page=1"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CineVerse-App/1.0'})
            with urllib.request.urlopen(req, timeout=6) as response:
                data = json.loads(response.read().decode('utf-8'))
                results = data.get('results', [])
                movies = []
                today = datetime.date.today()

                for item in results[:limit]:
                    title = item.get('title') or item.get('original_title')
                    if not title:
                        continue

                    genre_ids = item.get('genre_ids', [])
                    genres = [cls.TMDB_GENRES.get(gid, "Điện Ảnh") for gid in genre_ids]
                    genre_str = ", ".join(genres) if genres else "Hành Động, Phiêu Lưu"

                    poster_path = item.get('poster_path')
                    poster_url = f"https://image.tmdb.org/t/p/original{poster_path}" if poster_path else "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba"

                    release_date_str = item.get('release_date')
                    try:
                        release_date = datetime.datetime.strptime(release_date_str, '%Y-%m-%d').date() if release_date_str else today
                    except ValueError:
                        release_date = today

                    vote_average = float(item.get('vote_average', 7.5))
                    rating = round(vote_average / 2, 1) if vote_average > 5 else round(vote_average, 1)

                    movies.append({
                        'title': title,
                        'description': item.get('overview') or f"Tác phẩm điện ảnh đặc sắc '{title}' đang công chiếu tại hệ thống rạp CineVerse.",
                        'genre': genre_str,
                        'duration': 120,
                        'rating': rating,
                        'formats': '2D, 3D, IMAX',
                        'poster_url': poster_url,
                        'trailer_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                        'release_date': release_date,
                        'end_date': release_date + datetime.timedelta(days=45),
                        'status': 'now_showing',
                        'age_rating': 'C16' if vote_average > 7.0 else 'P',
                        'director': 'Đạo diễn Quốc Tế',
                        'cast': 'Dàn diễn viên Hollywood / Việt Nam',
                    })
                return movies
        except Exception as e:
            logger.warning(f"Error fetching from TMDB: {e}")
            return None

    @classmethod
    def fetch_from_tvmaze(cls, limit: int = 10) -> Optional[List[dict]]:
        """Fetch popular shows from TVMaze API (public, no key required)."""
        url = "https://api.tvmaze.com/shows?page=1"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CineVerse-App/1.0'})
            with urllib.request.urlopen(req, timeout=6) as response:
                items = json.loads(response.read().decode('utf-8'))
                movies = []
                today = datetime.date.today()

                for item in items[:limit]:
                    title = item.get('name')
                    if not title:
                        continue

                    raw_summary = item.get('summary') or ''
                    clean_summary = re.sub(r'<[^>]+>', '', raw_summary).strip()
                    if not clean_summary:
                        clean_summary = f"Bộ phim '{title}' hấp dẫn và kịch tính, đang chiếu trên toàn quốc."

                    genres = item.get('genres') or ['Drama']
                    genre_str = ", ".join(genres)

                    image_data = item.get('image') or {}
                    poster_url = image_data.get('original') or image_data.get('medium') or "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba"

                    runtime = item.get('runtime') or item.get('averageRuntime') or 115
                    rating_data = item.get('rating') or {}
                    rating_val = float(rating_data.get('average') or 8.0)
                    rating = round(rating_val / 2, 1) if rating_val > 5 else round(rating_val, 1)

                    premiered = item.get('premiered')
                    try:
                        release_date = datetime.datetime.strptime(premiered, '%Y-%m-%d').date() if premiered else today
                    except ValueError:
                        release_date = today

                    movies.append({
                        'title': title,
                        'description': clean_summary,
                        'genre': genre_str,
                        'duration': int(runtime),
                        'rating': rating,
                        'formats': '2D, 3D',
                        'poster_url': poster_url,
                        'trailer_url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                        'release_date': release_date,
                        'end_date': today + datetime.timedelta(days=45),
                        'status': 'now_showing',
                        'age_rating': 'C13',
                        'director': 'Đạo diễn Quốc Tế',
                        'cast': 'Dàn diễn viên điện ảnh',
                    })
                return movies
        except Exception as e:
            logger.warning(f"Error fetching from TVMaze: {e}")
            return None

    @classmethod
    def get_curated_fallback(cls, limit: int = 10) -> List[dict]:
        """Curated high-definition catalog of trending cinema movies."""
        today = datetime.date.today()
        catalog = [
            {
                'title': 'Dune: Hành Tinh Cát - Phần 2',
                'description': 'Paul Atreides hợp nhất với Chani và người Fremen trên con đường tìm kiếm sự báo thù chống lại những kẻ đã hủy hoại gia đình anh, đối mặt với sự lựa chọn giữa tình yêu và số phận vũ trụ.',
                'genre': 'Khoa Học Viễn Tưởng, Phiêu Lưu, Hành Động',
                'duration': 166,
                'rating': 4.9,
                'formats': '2D, 3D, IMAX',
                'poster_url': 'https://image.tmdb.org/t/p/original/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg',
                'trailer_url': 'https://www.youtube.com/embed/Way9Dexny3w',
                'release_date': today - datetime.timedelta(days=10),
                'end_date': today + datetime.timedelta(days=45),
                'status': 'now_showing',
                'age_rating': 'C16',
                'director': 'Denis Villeneuve',
                'cast': 'Timothée Chalamet, Zendaya, Rebecca Ferguson, Javier Bardem',
            },
            {
                'title': 'Mai',
                'description': 'Câu chuyện tình yêu đầy trắc trở giữa Mai - một người phụ nữ làm nghề massage trị liệu và Dương - một chàng trai đào hoa trẻ tuổi, qua góc nhìn nhân văn sâu sắc của đạo diễn Trấn Thành.',
                'genre': 'Tâm Lý, Tình Cảm, Gia Đình',
                'duration': 131,
                'rating': 4.7,
                'formats': '2D',
                'poster_url': 'https://image.tmdb.org/t/p/original/y4H7a5b3a3qW4qR6GzRzZkM3tQZ.jpg',
                'trailer_url': 'https://www.youtube.com/embed/pCqK5dI1N_k',
                'release_date': today - datetime.timedelta(days=15),
                'end_date': today + datetime.timedelta(days=30),
                'status': 'now_showing',
                'age_rating': 'C18',
                'director': 'Trấn Thành',
                'cast': 'Phương Anh Đào, Tuấn Trần, Trấn Thành, Hồng Đào',
            },
            {
                'title': 'Godzilla x Kong: Đế Chế Mới',
                'description': 'Hai quái thú huyền thoại Godzilla và Kong hợp sức chống lại một mối đe dọa khổng lồ ẩn sâu bên trong Trái Đất Rỗng, thách thức sự tồn vong của loài người.',
                'genre': 'Hành Động, Quái Thú, Khoa Học Viễn Tưởng',
                'duration': 115,
                'rating': 4.6,
                'formats': '2D, 3D, IMAX',
                'poster_url': 'https://image.tmdb.org/t/p/original/bQ2ywkchCe02uqVo2LsgxTmumip.jpg',
                'trailer_url': 'https://www.youtube.com/embed/lV1OOlGwExM',
                'release_date': today - datetime.timedelta(days=5),
                'end_date': today + datetime.timedelta(days=50),
                'status': 'now_showing',
                'age_rating': 'C13',
                'director': 'Adam Wingard',
                'cast': 'Rebecca Hall, Brian Tyree Henry, Dan Stevens',
            },
            {
                'title': 'Deadpool & Wolverine',
                'description': 'Deadpool phải hợp tác với Wolverine để cứu vũ trụ của mình trong một cuộc phiêu lưu hỗn loạn, hài hước và bùng nổ đầy hành động đẫm máu.',
                'genre': 'Hành Động, Hài Hước, Siêu Anh Hùng',
                'duration': 127,
                'rating': 4.8,
                'formats': '2D, 3D, IMAX',
                'poster_url': 'https://image.tmdb.org/t/p/original/8cdWjvZQUExUUTzyp4t6EDMubfO.jpg',
                'trailer_url': 'https://www.youtube.com/embed/73_1biulkYk',
                'release_date': today - datetime.timedelta(days=2),
                'end_date': today + datetime.timedelta(days=60),
                'status': 'now_showing',
                'age_rating': 'C18',
                'director': 'Shawn Levy',
                'cast': 'Ryan Reynolds, Hugh Jackman, Emma Corrin, Matthew Macfadyen',
            },
            {
                'title': 'Những Mảnh Ghép Cảm Xúc 2 (Inside Out 2)',
                'description': 'Trở lại tâm trí của cô bé tuổi teen Riley vừa bước vào tuổi dậy thì, chào đón những cảm xúc mới: Lo Âu (Anxiety), Ghen Tị (Envy), Ngượng Ngùng (Embarrassment) và Chán Nản (Ennui).',
                'genre': 'Hoạt Hình, Gia Đình, Hài Hước',
                'duration': 96,
                'rating': 4.8,
                'formats': '2D, 3D',
                'poster_url': 'https://image.tmdb.org/t/p/original/vpnVM9B6NMmQpWeZvzLvDESb2QY.jpg',
                'trailer_url': 'https://www.youtube.com/embed/LEjhY15eCx0',
                'release_date': today - datetime.timedelta(days=8),
                'end_date': today + datetime.timedelta(days=40),
                'status': 'now_showing',
                'age_rating': 'P',
                'director': 'Kelsey Mann',
                'cast': 'Amy Poehler, Maya Hawke, Phyllis Smith, Lewis Black',
            },
            {
                'title': 'Kẻ Trộm Mặt Trăng 4 (Despicable Me 4)',
                'description': 'Gru và gia đình đối mặt với kẻ thù mới nguy hiểm Maxime Le Mal và bạn gái quyến rũ Valentina, khiến cả gia đình phải lẩn trốn trong khi biệt đội Mega Minions xuất trận.',
                'genre': 'Hoạt Hình, Phiêu Lưu, Hài Hước',
                'duration': 95,
                'rating': 4.5,
                'formats': '2D, 3D',
                'poster_url': 'https://image.tmdb.org/t/p/original/wWba3TaojhK7NdycRhoQpsG0FaH.jpg',
                'trailer_url': 'https://www.youtube.com/embed/qQlr9-rF32A',
                'release_date': today - datetime.timedelta(days=12),
                'end_date': today + datetime.timedelta(days=35),
                'status': 'now_showing',
                'age_rating': 'P',
                'director': 'Chris Renaud',
                'cast': 'Steve Carell, Kristen Wiig, Will Ferrell, Sofia Vergara',
            },
            {
                'title': 'Oppenheimer',
                'description': 'Câu chuyện lịch sử về nhà vật lý lý thuyết J. Robert Oppenheimer, người lãnh đạo Dự án Manhattan chế tạo quả bom nguyên tử đầu tiên trong Thế chiến thứ hai.',
                'genre': 'Tiểu Sử, Lịch Sử, Chính Kịch',
                'duration': 180,
                'rating': 4.9,
                'formats': '2D, IMAX',
                'poster_url': 'https://image.tmdb.org/t/p/original/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg',
                'trailer_url': 'https://www.youtube.com/embed/uYPbbksJxIg',
                'release_date': today - datetime.timedelta(days=30),
                'end_date': today + datetime.timedelta(days=20),
                'status': 'now_showing',
                'age_rating': 'C18',
                'director': 'Christopher Nolan',
                'cast': 'Cillian Murphy, Emily Blunt, Matt Damon, Robert Downey Jr.',
            },
            {
                'title': 'Lật Mặt 7: Một Điều Ước',
                'description': 'Bà Hai 73 tuổi sống một mình tại ngôi làng hẻo lánh. Sau một tai nạn, năm người con ở khắp các miền đất nước phải bàn bạc ai sẽ là người chăm sóc mẹ.',
                'genre': 'Tâm Lý, Tình Cảm, Gia Đình',
                'duration': 138,
                'rating': 4.8,
                'formats': '2D',
                'poster_url': 'https://image.tmdb.org/t/p/original/4yF7b6Rk7mQ0tO7jS9Z3K1m2n3p.jpg',
                'trailer_url': 'https://www.youtube.com/embed/d2W_oK3zGgM',
                'release_date': today - datetime.timedelta(days=20),
                'end_date': today + datetime.timedelta(days=25),
                'status': 'now_showing',
                'age_rating': 'K',
                'director': 'Lý Hải',
                'cast': 'Thanh Hiền, Trương Minh Cường, Đinh Y Nhung, Quách Ngọc Tuyên',
            }
        ]
        return catalog[:limit]

    @classmethod
    @transaction.atomic
    def sync_now_playing_movies(cls, limit: int = 10, source: str = 'auto') -> dict:
        """
        Synchronize now-playing movie catalog into database.
        
        Args:
            limit: Maximum number of movies to sync.
            source: 'auto' | 'tmdb' | 'tvmaze' | 'curated'
            
        Returns:
            dict containing sync summary and affected movie titles.
        """
        logger.info(f"Starting movie sync with source={source}, limit={limit}")
        movies_data = None
        used_source = source

        if source == 'tmdb':
            movies_data = cls.fetch_from_tmdb(limit)
        elif source == 'tvmaze':
            movies_data = cls.fetch_from_tvmaze(limit)
        elif source == 'curated':
            movies_data = cls.get_curated_fallback(limit)
        else:  # auto
            movies_data = cls.fetch_from_tmdb(limit)
            if movies_data:
                used_source = 'TMDB API'
            else:
                movies_data = cls.fetch_from_tvmaze(limit)
                if movies_data:
                    used_source = 'TVMaze API (Free Open Fallback)'
                else:
                    movies_data = cls.get_curated_fallback(limit)
                    used_source = 'Curated Cinema Blockbusters Fallback'

        if not movies_data:
            movies_data = cls.get_curated_fallback(limit)
            used_source = 'Curated Cinema Blockbusters Fallback'

        synced_titles = []
        created_count = 0
        updated_count = 0

        for m_data in movies_data[:limit]:
            title = m_data.pop('title')
            movie, created = Movie.objects.update_or_create(
                title=title,
                defaults=m_data
            )
            synced_titles.append(movie.title)
            if created:
                created_count += 1
            else:
                updated_count += 1

        logger.info(f"Movie sync completed: {created_count} created, {updated_count} updated via {used_source}")
        return {
            'success': True,
            'source': used_source,
            'count': len(synced_titles),
            'created_count': created_count,
            'updated_count': updated_count,
            'movies': synced_titles
        }

