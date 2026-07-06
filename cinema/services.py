"""
Cinema Service Layer - Business Logic (Service Pattern).

This module contains all business rules and workflow orchestration,
delegating data access to the Repository layer and design pattern
execution to the Patterns module.
"""

import logging
import datetime
from typing import Optional, List, Tuple
from django.db import transaction

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
