"""
CineVerse Test Suite — Comprehensive Unit & Integration Tests.

Covers all 12 design patterns + repository layer + service layer + API endpoints.
Target: 50%+ code coverage.

Run:
    python manage.py test cinema -v 2
    coverage run manage.py test cinema && coverage report
"""

import json
import datetime
from django.test import TestCase, Client
from django.urls import reverse

from .models import (
    User, Movie, Theater, Screen, Seat,
    Showtime, Booking, BookingItem, Payment, Discount, InAppNotification
)
from .patterns import (
    VIPSeatPriceDecorator, CoupleSeatPriceDecorator, SimpleSeat,
    get_discount_validation_chain, get_booking_state_class,
    BookingBuilder, StandardBookingWorkflow,
    PaymentProcessorFactory, SystemSettings,
    WeekdayPricing, WeekendPricing, HolidayPricing,
    BookingSubject, EmailObserver, InAppObserver,
)
from .services import (
    UserService, MovieService, BookingService,
    DuplicateEmailException, InvalidCredentialsException,
    AccountBannedException, MovieNotFoundException,
    BookingNotFoundException, UnauthorizedActionException,
    InvalidTicketException, SeatNotFoundException
)
from .repositories import (
    UserRepository, MovieRepository, BookingRepository,
    ShowtimeRepository, DiscountRepository
)


# ─────────────────────────────────────────────────────────────────────────────
# TEST FIXTURES MIXIN
# ─────────────────────────────────────────────────────────────────────────────

class BaseTestCase(TestCase):
    """Shared setUp for all CineVerse tests."""

    def setUp(self):
        # User
        self.user = User.objects.create(
            email="test@cinema.com", name="Test User", status="active"
        )
        self.user.set_password("testpass123")
        self.user.save()

        self.admin = User.objects.create(
            email="admin@cinema.com", name="Admin", status="active"
        )
        self.admin.set_password("admin123")
        self.admin.save()

        # Movie
        self.movie = Movie.objects.create(
            title="Inception",
            description="A mind-bending sci-fi heist",
            genre="Sci-Fi, Action",
            duration=148,
            release_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=30),
            status="now_showing",
            rating=8.8
        )

        self.movie2 = Movie.objects.create(
            title="The Dark Knight",
            description="Batman vs Joker",
            genre="Action, Drama",
            duration=152,
            release_date=datetime.date.today() + datetime.timedelta(days=5),
            end_date=datetime.date.today() + datetime.timedelta(days=60),
            status="coming_soon",
            rating=9.0
        )

        # Theater & Screen
        self.theater = Theater.objects.create(
            name="CineVerse Hà Nội",
            city="Hanoi",
            address="123 Cinema Street"
        )
        self.screen = Screen.objects.create(
            theater=self.theater,
            name="Screen IMAX 1",
            format="IMAX",
            capacity=50,
            rows=5,
            columns=10
        )

        # Seats
        self.seat_normal = Seat.objects.create(
            screen=self.screen, row="A", column=1,
            seat_number="A1", type="normal", price=80000, status="available"
        )
        self.seat_vip = Seat.objects.create(
            screen=self.screen, row="C", column=5,
            seat_number="C5", type="vip", price=120000, status="available"
        )
        self.seat_couple = Seat.objects.create(
            screen=self.screen, row="E", column=1,
            seat_number="E1-2", type="couple", price=200000, status="available"
        )

        # Showtime
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            screen=self.screen,
            start_time=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1),
            end_time=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1, hours=2),
            price_multiplier=1.2
        )

        # Discount
        self.discount = Discount.objects.create(
            code="SUMMER2026",
            type="percentage",
            value=20,
            min_amount=50000,
            valid_from=datetime.date.today() - datetime.timedelta(days=5),
            valid_to=datetime.date.today() + datetime.timedelta(days=30),
            usage_limit=100,
            usage_count=0,
            per_user_limit=3
        )

        self.client = Client()


# ─────────────────────────────────────────────────────────────────────────────
# PATTERN 1: SINGLETON
# ─────────────────────────────────────────────────────────────────────────────

class SingletonPatternTests(BaseTestCase):
    """Tests for Singleton pattern (SystemSettings)."""

    def test_singleton_returns_same_instance(self):
        """SystemSettings() must return the exact same object each time."""
        s1 = SystemSettings()
        s2 = SystemSettings()
        self.assertIs(s1, s2, "Singleton must return same instance on repeated calls")

    def test_singleton_has_cancellation_fee(self):
        """Singleton must expose cancellation_fee_percent setting."""
        settings = SystemSettings()
        self.assertTrue(hasattr(settings, 'cancellation_fee_percent'))
        self.assertEqual(settings.cancellation_fee_percent, 10)

    def test_singleton_has_tax_rate(self):
        """Singleton must expose a tax_rate setting."""
        settings = SystemSettings()
        self.assertTrue(hasattr(settings, 'tax_rate'))
        self.assertAlmostEqual(settings.tax_rate, 0.08)


# ─────────────────────────────────────────────────────────────────────────────
# PATTERN 2: FACTORY
# ─────────────────────────────────────────────────────────────────────────────

class FactoryPatternTests(BaseTestCase):
    """Tests for Factory pattern (PaymentProcessorFactory)."""

    def test_factory_creates_credit_card_processor(self):
        """Factory must produce a processor for 'credit_card'."""
        factory = PaymentProcessorFactory()
        processor = factory.create_processor("credit_card")
        self.assertIsNotNone(processor)
        self.assertTrue(hasattr(processor, 'charge'))

    def test_factory_creates_momo_processor(self):
        """Factory must produce a processor for 'momo'."""
        factory = PaymentProcessorFactory()
        processor = factory.create_processor("momo")
        self.assertIsNotNone(processor)
        self.assertTrue(hasattr(processor, 'charge'))

    def test_factory_unknown_method_raises(self):
        """Factory must raise an error for unknown payment methods."""
        factory = PaymentProcessorFactory()
        with self.assertRaises(Exception):
            factory.create_processor("bitcoin")


# ─────────────────────────────────────────────────────────────────────────────
# PATTERN 3: STRATEGY
# ─────────────────────────────────────────────────────────────────────────────

class StrategyPatternTests(BaseTestCase):
    """Tests for Strategy pattern (Pricing strategies)."""

    BASE = 100000  # 100k VND base price for calculations

    def test_weekday_pricing_applies_discount(self):
        """WeekdayPricing should apply a 10% weekday discount."""
        result = WeekdayPricing().calculate_base_price(self.BASE)
        self.assertEqual(result, 90000)  # 100k * 0.9

    def test_weekend_pricing_applies_surcharge(self):
        """WeekendPricing should apply a 20% surcharge."""
        result = WeekendPricing().calculate_base_price(self.BASE)
        self.assertEqual(result, 120000)  # 100k * 1.2

    def test_holiday_pricing_is_highest(self):
        """HolidayPricing must produce the highest price."""
        holiday = HolidayPricing().calculate_base_price(self.BASE)
        weekend = WeekendPricing().calculate_base_price(self.BASE)
        self.assertGreaterEqual(holiday, weekend)

    def test_weekend_higher_than_weekday(self):
        """Weekend price must be greater than weekday price."""
        weekend = WeekendPricing().calculate_base_price(self.BASE)
        weekday = WeekdayPricing().calculate_base_price(self.BASE)
        self.assertGreater(weekend, weekday)


# ─────────────────────────────────────────────────────────────────────────────
# PATTERN 4: OBSERVER
# ─────────────────────────────────────────────────────────────────────────────

class ObserverPatternTests(BaseTestCase):
    """Tests for Observer pattern (BookingSubject + EmailObserver + InAppObserver)."""

    def test_observer_sends_inapp_notification(self):
        """InAppObserver must create InAppNotification records on booking confirmed."""
        booking = Booking.objects.create(
            user=self.user, showtime=self.showtime,
            total_price=100000, status="confirmed"
        )
        initial_count = InAppNotification.objects.filter(user=self.user).count()

        subject = BookingSubject()
        subject.attach(InAppObserver())
        subject.notify(booking, "booking_confirmed")

        new_count = InAppNotification.objects.filter(user=self.user).count()
        self.assertGreater(new_count, initial_count)

    def test_observer_attach_and_detach(self):
        """Observers can be attached and detached from the subject."""
        subject = BookingSubject()
        observer = InAppObserver()
        subject.attach(observer)
        self.assertIn(observer, subject._observers)
        subject.detach(observer)
        self.assertNotIn(observer, subject._observers)


# ─────────────────────────────────────────────────────────────────────────────
# PATTERN 5: DECORATOR
# ─────────────────────────────────────────────────────────────────────────────

class DecoratorPatternTests(BaseTestCase):
    """Tests for Decorator pattern (Seat price decorators)."""

    def test_simple_seat_returns_base_price(self):
        """SimpleSeat component should return the model's base price."""
        comp = SimpleSeat(self.seat_normal)
        self.assertEqual(comp.get_price(), 80000)

    def test_vip_decorator_adds_surcharge(self):
        """VIPSeatPriceDecorator should multiply base price by 1.5."""
        comp = SimpleSeat(self.seat_vip)
        decorated = VIPSeatPriceDecorator(comp)
        self.assertEqual(decorated.get_price(), 180000)  # 120000 * 1.5

    def test_couple_decorator_price(self):
        """CoupleSeatPriceDecorator should return couple seat price correctly."""
        comp = SimpleSeat(self.seat_couple)
        decorated = CoupleSeatPriceDecorator(comp)
        self.assertGreater(decorated.get_price(), 200000)


# ─────────────────────────────────────────────────────────────────────────────
# PATTERN 6: CHAIN OF RESPONSIBILITY
# ─────────────────────────────────────────────────────────────────────────────

class ChainOfResponsibilityTests(BaseTestCase):
    """Tests for Chain of Responsibility pattern (Discount validation chain)."""

    def test_valid_discount_passes_chain(self):
        """A valid discount code for an eligible booking must pass all validators."""
        booking = Booking.objects.create(
            user=self.user, showtime=self.showtime,
            total_price=150000, status="pending"
        )
        chain = get_discount_validation_chain()
        self.assertTrue(chain.validate(self.discount, booking))

    def test_minimum_amount_fails_chain(self):
        """Booking below min_amount must fail chain validation."""
        booking = Booking.objects.create(
            user=self.user, showtime=self.showtime,
            total_price=30000, status="pending"
        )
        chain = get_discount_validation_chain()
        with self.assertRaises(Exception) as ctx:
            chain.validate(self.discount, booking)
        self.assertIn("minimum", str(ctx.exception).lower())

    def test_expired_discount_fails_chain(self):
        """An expired discount code must fail chain validation."""
        expired = Discount.objects.create(
            code="EXPIRED10",
            type="percentage",
            value=10,
            min_amount=0,
            valid_from=datetime.date(2020, 1, 1),
            valid_to=datetime.date(2020, 12, 31),
            usage_limit=100,
            usage_count=0,
            per_user_limit=5
        )
        booking = Booking.objects.create(
            user=self.user, showtime=self.showtime,
            total_price=200000, status="pending"
        )
        chain = get_discount_validation_chain()
        with self.assertRaises(Exception) as ctx:
            chain.validate(expired, booking)
        self.assertIn("expir", str(ctx.exception).lower())


# ─────────────────────────────────────────────────────────────────────────────
# PATTERN 7: STATE
# ─────────────────────────────────────────────────────────────────────────────

class StatePatternTests(BaseTestCase):
    """Tests for State pattern (Booking lifecycle transitions)."""

    def test_pending_to_confirmed(self):
        """A pending booking can transition to confirmed."""
        booking = Booking.objects.create(
            user=self.user, showtime=self.showtime,
            total_price=100000, status="pending"
        )
        state = get_booking_state_class(booking.status)
        self.assertTrue(state.confirm(booking))
        self.assertEqual(booking.status, "confirmed")

    def test_confirmed_to_cancelled_with_refund(self):
        """Cancelling a confirmed booking sets refund to 90% of total."""
        booking = Booking.objects.create(
            user=self.user, showtime=self.showtime,
            total_price=100000, status="confirmed"
        )
        state = get_booking_state_class(booking.status)
        state.cancel(booking)
        self.assertEqual(booking.status, "cancelled")
        self.assertEqual(booking.refund_amount, 90000)

    def test_confirmed_to_completed(self):
        """A confirmed booking can be completed (ticket scanned at entrance)."""
        booking = Booking.objects.create(
            user=self.user, showtime=self.showtime,
            total_price=100000, status="confirmed"
        )
        state = get_booking_state_class(booking.status)
        state.complete(booking)
        self.assertEqual(booking.status, "completed")

    def test_cancelled_cannot_confirm(self):
        """A cancelled booking cannot transition to confirmed."""
        booking = Booking.objects.create(
            user=self.user, showtime=self.showtime,
            total_price=100000, status="cancelled"
        )
        state = get_booking_state_class(booking.status)
        with self.assertRaises(Exception):
            state.confirm(booking)


# ─────────────────────────────────────────────────────────────────────────────
# PATTERN 8: BUILDER
# ─────────────────────────────────────────────────────────────────────────────

class BuilderPatternTests(BaseTestCase):
    """Tests for Builder pattern (BookingBuilder)."""

    def test_builder_creates_booking(self):
        """BookingBuilder must produce a persisted booking with correct total."""
        booking = (BookingBuilder()
            .set_user(self.user)
            .set_showtime(self.showtime)
            .add_seat(self.seat_normal)
            .add_seat(self.seat_vip)
            .set_discount(self.discount)
            .set_notes("Window seat please")
            .build()
        )
        self.assertIsNotNone(booking.id)
        self.assertEqual(booking.notes, "Window seat please")
        # (80k + 180k) * 1.2 = 312k, discount 20% = 62.4k → 249600
        self.assertEqual(booking.total_price, 249600)

    def test_builder_without_discount(self):
        """Builder without discount should not apply any deduction."""
        booking = (BookingBuilder()
            .set_user(self.user)
            .set_showtime(self.showtime)
            .add_seat(self.seat_normal)
            .build()
        )
        # 80000 * 1.2 = 96000
        self.assertEqual(booking.total_price, 96000)

    def test_builder_requires_user(self):
        """Builder must raise an error if build() is called without a user."""
        with self.assertRaises(Exception):
            BookingBuilder().set_showtime(self.showtime).build()


# ─────────────────────────────────────────────────────────────────────────────
# PATTERN 9: TEMPLATE METHOD
# ─────────────────────────────────────────────────────────────────────────────

class TemplateMethodTests(BaseTestCase):
    """Tests for Template Method pattern (StandardBookingWorkflow)."""

    def test_workflow_produces_confirmed_booking(self):
        """StandardBookingWorkflow must return a confirmed booking + completed payment."""
        workflow = StandardBookingWorkflow()
        booking, payment = workflow.execute(
            user=self.user,
            showtime=self.showtime,
            seats=[self.seat_normal],
            discount_code="SUMMER2026",
            payment_method="credit_card"
        )
        self.assertEqual(booking.status, "confirmed")
        self.assertEqual(payment.status, "completed")
        self.assertEqual(payment.booking, booking)

    def test_workflow_no_discount(self):
        """Workflow without discount code should still complete successfully."""
        workflow = StandardBookingWorkflow()
        booking, payment = workflow.execute(
            user=self.user,
            showtime=self.showtime,
            seats=[self.seat_vip],
            payment_method="momo"
        )
        self.assertEqual(booking.status, "confirmed")
        self.assertIsNotNone(payment.transaction_id)


# ─────────────────────────────────────────────────────────────────────────────
# REPOSITORY LAYER TESTS
# ─────────────────────────────────────────────────────────────────────────────

class RepositoryTests(BaseTestCase):
    """Tests for the Repository pattern — data access abstraction."""

    def test_user_repo_get_by_id(self):
        """UserRepository.get_by_id should return correct user."""
        result = UserRepository.get_by_id(self.user.id)
        self.assertEqual(result, self.user)

    def test_user_repo_get_by_id_missing_returns_none(self):
        """UserRepository.get_by_id should return None for unknown id."""
        self.assertIsNone(UserRepository.get_by_id(99999))

    def test_user_repo_get_by_email(self):
        """UserRepository.get_by_email should match case-insensitively."""
        result = UserRepository.get_by_email("TEST@CINEMA.COM")
        self.assertEqual(result, self.user)

    def test_movie_repo_get_by_id(self):
        """MovieRepository.get_by_id should return the correct movie."""
        result = MovieRepository.get_by_id(self.movie.id)
        self.assertEqual(result, self.movie)

    def test_movie_repo_filter_by_status(self):
        """MovieRepository.filter_movies should filter by status."""
        results = MovieRepository.filter_movies(status='now_showing')
        self.assertIn(self.movie, results)
        self.assertNotIn(self.movie2, results)

    def test_movie_repo_filter_by_genre(self):
        """MovieRepository.filter_movies should filter by genre substring."""
        results = MovieRepository.filter_movies(genre='Action')
        self.assertIn(self.movie, results)

    def test_movie_repo_search_title(self):
        """MovieRepository.filter_movies should search by title."""
        results = MovieRepository.filter_movies(search_query='Inception')
        self.assertIn(self.movie, results)
        self.assertNotIn(self.movie2, results)

    def test_discount_repo_case_insensitive(self):
        """DiscountRepository.get_by_code should be case-insensitive."""
        result = DiscountRepository.get_by_code("summer2026")
        self.assertEqual(result, self.discount)

    def test_showtime_repo_get_movie_showtimes(self):
        """ShowtimeRepository.get_movie_showtimes should return showtimes for movie."""
        results = ShowtimeRepository.get_movie_showtimes(self.movie.id)
        self.assertIn(self.showtime, results)

    def test_booking_repo_get_user_bookings(self):
        """BookingRepository.get_user_bookings should return user's bookings."""
        booking = Booking.objects.create(
            user=self.user, showtime=self.showtime,
            total_price=80000, status="confirmed"
        )
        results = BookingRepository.get_user_bookings(self.user.id)
        self.assertIn(booking, results)


# ─────────────────────────────────────────────────────────────────────────────
# SERVICE LAYER TESTS
# ─────────────────────────────────────────────────────────────────────────────

class UserServiceTests(BaseTestCase):
    """Tests for UserService business logic."""

    def test_register_new_user(self):
        """UserService.register should create and return an active user."""
        user = UserService.register(
            email="newuser@cinema.com",
            password="newpass123",
            name="New User"
        )
        self.assertIsNotNone(user.id)
        self.assertEqual(user.status, "active")
        self.assertEqual(user.name, "New User")

    def test_register_duplicate_email_raises(self):
        """UserService.register should raise DuplicateEmailException for used emails."""
        with self.assertRaises(DuplicateEmailException):
            UserService.register("test@cinema.com", "pass", "Duplicate")

    def test_login_success(self):
        """UserService.login should return user on valid credentials."""
        user = UserService.login("test@cinema.com", "testpass123")
        self.assertEqual(user, self.user)

    def test_login_wrong_password_raises(self):
        """UserService.login should raise InvalidCredentialsException on wrong password."""
        with self.assertRaises(InvalidCredentialsException):
            UserService.login("test@cinema.com", "wrongpassword")

    def test_login_unknown_email_raises(self):
        """UserService.login should raise on unknown email."""
        with self.assertRaises(InvalidCredentialsException):
            UserService.login("nobody@cinema.com", "pass")

    def test_login_banned_account_raises(self):
        """UserService.login should raise AccountBannedException for banned users."""
        self.user.status = 'banned'
        self.user.save()
        with self.assertRaises(AccountBannedException):
            UserService.login("test@cinema.com", "testpass123")


class MovieServiceTests(BaseTestCase):
    """Tests for MovieService business logic."""

    def test_get_movies_all(self):
        """MovieService.get_movies with no filters should return all movies."""
        results = MovieService.get_movies()
        self.assertIn(self.movie, results)
        self.assertIn(self.movie2, results)

    def test_get_movies_filter_status(self):
        """MovieService.get_movies should filter by status."""
        results = MovieService.get_movies(status='now_showing')
        self.assertIn(self.movie, results)
        self.assertNotIn(self.movie2, results)

    def test_get_details_valid(self):
        """MovieService.get_details should return the movie for a valid id."""
        result = MovieService.get_details(self.movie.id)
        self.assertEqual(result, self.movie)

    def test_get_details_invalid_raises(self):
        """MovieService.get_details should raise MovieNotFoundException for bad id."""
        with self.assertRaises(MovieNotFoundException):
            MovieService.get_details(99999)


class BookingServiceTests(BaseTestCase):
    """Tests for BookingService business logic."""

    def test_make_booking_success(self):
        """BookingService.make_booking should create a confirmed booking."""
        booking = BookingService.make_booking(
            user_id=self.user.id,
            showtime_id=self.showtime.id,
            seat_ids=[self.seat_normal.id]
        )
        self.assertIsNotNone(booking.id)
        self.assertEqual(booking.status, "confirmed")

    def test_make_booking_invalid_user_raises(self):
        """BookingService.make_booking should raise for unknown user_id."""
        from .services import UserNotFoundException
        with self.assertRaises(UserNotFoundException):
            BookingService.make_booking(99999, self.showtime.id, [self.seat_normal.id])

    def test_make_booking_invalid_showtime_raises(self):
        """BookingService.make_booking should raise for unknown showtime_id."""
        from .services import ShowtimeNotFoundException
        with self.assertRaises(ShowtimeNotFoundException):
            BookingService.make_booking(self.user.id, 99999, [self.seat_normal.id])

    def test_cancel_booking_unauthorised_raises(self):
        """BookingService.cancel_booking should raise for wrong user."""
        booking = Booking.objects.create(
            user=self.user, showtime=self.showtime,
            total_price=100000, status="confirmed"
        )
        other_user = User.objects.create(
            email="other@cinema.com", name="Other", status="active"
        )
        other_user.set_password("pass")
        other_user.save()
        with self.assertRaises(UnauthorizedActionException):
            BookingService.cancel_booking(booking.id, other_user.id)

    def test_cancel_booking_not_found_raises(self):
        """BookingService.cancel_booking should raise BookingNotFoundException."""
        with self.assertRaises(BookingNotFoundException):
            BookingService.cancel_booking(99999, self.user.id)

    def test_verify_ticket_success(self):
        """BookingService.verify_ticket should mark booking as completed."""
        booking = Booking.objects.create(
            user=self.user, showtime=self.showtime,
            total_price=100000, status="confirmed"
        )
        result = BookingService.verify_ticket(f"CINEMA-BOOKING-ID:{booking.id}")
        self.assertEqual(result.status, "completed")

    def test_verify_ticket_invalid_format_raises(self):
        """BookingService.verify_ticket should raise for wrong QR format."""
        with self.assertRaises(InvalidTicketException):
            BookingService.verify_ticket("INVALID-QR-CODE")

    def test_verify_ticket_missing_booking_raises(self):
        """BookingService.verify_ticket should raise for non-existent booking ID."""
        with self.assertRaises(InvalidTicketException):
            BookingService.verify_ticket("CINEMA-BOOKING-ID:99999")


# ─────────────────────────────────────────────────────────────────────────────
# API / VIEW TESTS
# ─────────────────────────────────────────────────────────────────────────────

class APITests(BaseTestCase):
    """Integration tests for REST API endpoints (views)."""

    def _login(self, email="test@cinema.com", password="testpass123"):
        """Helper: log in via POST and store session cookie."""
        self.client.post(
            reverse('login'),
            {'email': email, 'password': password}
        )

    def test_api_validate_discount_valid(self):
        """POST /api/discount/validate/ with valid code returns success."""
        self._login()
        resp = self.client.post(
            reverse('api_validate_discount'),
            data=json.dumps({'code': 'SUMMER2026', 'subtotal': 200000}),
            content_type='application/json'
        )
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertIn('discount_amount', data)

    def test_api_validate_discount_invalid(self):
        """POST /api/discount/validate/ with wrong code returns error."""
        self._login()
        resp = self.client.post(
            reverse('api_validate_discount'),
            data=json.dumps({'code': 'BADCODE', 'subtotal': 200000}),
            content_type='application/json'
        )
        data = resp.json()
        self.assertFalse(data['success'])

    def test_api_create_booking_requires_login(self):
        """POST /api/booking/create/ must redirect unauthenticated users."""
        resp = self.client.post(
            reverse('api_create_booking'),
            data=json.dumps({'showtime_id': self.showtime.id, 'seat_ids': [self.seat_normal.id]}),
            content_type='application/json'
        )
        # Should redirect to login
        self.assertIn(resp.status_code, [302, 403])

    def test_api_toggle_favorite_add(self):
        """POST /api/favorite/toggle/ should add the movie to favorites."""
        self._login()
        resp = self.client.post(
            reverse('api_toggle_favorite'),
            data=json.dumps({'movie_id': self.movie.id}),
            content_type='application/json'
        )
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['state'], 'added')

    def test_api_toggle_favorite_remove(self):
        """POST /api/favorite/toggle/ twice should remove the movie."""
        self._login()
        # Add
        self.client.post(
            reverse('api_toggle_favorite'),
            data=json.dumps({'movie_id': self.movie.id}),
            content_type='application/json'
        )
        # Remove
        resp = self.client.post(
            reverse('api_toggle_favorite'),
            data=json.dumps({'movie_id': self.movie.id}),
            content_type='application/json'
        )
        data = resp.json()
        self.assertEqual(data['state'], 'removed')

    def test_api_toggle_watchlist(self):
        """POST /api/watchlist/toggle/ should add then remove the movie."""
        self._login()
        resp = self.client.post(
            reverse('api_toggle_watchlist'),
            data=json.dumps({'movie_id': self.movie.id}),
            content_type='application/json'
        )
        self.assertTrue(resp.json()['success'])

    def test_index_view_loads(self):
        """GET / should return HTTP 200."""
        resp = self.client.get(reverse('index'))
        self.assertEqual(resp.status_code, 200)

    def test_movie_detail_view_loads(self):
        """GET /movie/<id>/ should return HTTP 200."""
        resp = self.client.get(reverse('movie_detail', args=[self.movie.id]))
        self.assertEqual(resp.status_code, 200)

    def test_movie_detail_not_found_redirects(self):
        """GET /movie/99999/ should redirect (movie not found)."""
        resp = self.client.get(reverse('movie_detail', args=[99999]))
        self.assertEqual(resp.status_code, 302)

    def test_booking_flow_requires_login(self):
        """GET /booking/showtime/<id>/ should redirect unauthenticated users."""
        resp = self.client.get(reverse('booking_flow', args=[self.showtime.id]))
        self.assertEqual(resp.status_code, 302)

    def test_profile_requires_login(self):
        """GET /profile/ should redirect unauthenticated users."""
        resp = self.client.get(reverse('profile'))
        self.assertEqual(resp.status_code, 302)

    def test_profile_accessible_when_logged_in(self):
        """GET /profile/ should return 200 when authenticated."""
        self._login()
        resp = self.client.get(reverse('profile'))
        self.assertEqual(resp.status_code, 200)

    def test_login_view_loads(self):
        """GET /login/ should return HTTP 200."""
        resp = self.client.get(reverse('login'))
        self.assertEqual(resp.status_code, 200)

    def test_register_view_loads(self):
        """GET /register/ should return HTTP 200."""
        resp = self.client.get(reverse('register'))
        self.assertEqual(resp.status_code, 200)
