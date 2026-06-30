"""
Cinema Repository Layer - Data Access Objects (Repository Pattern).

This module abstracts all direct ORM queries from service logic,
following the Repository Design Pattern for clean separation of concerns.
"""

import logging
from typing import Optional, List
from django.db.models import Q, QuerySet
from .models import (
    User, Movie, Theater, Screen, Seat,
    Showtime, Booking, BookingItem, Payment,
    Review, Discount, Favorite, Watchlist,
    Address, InAppNotification
)

logger = logging.getLogger(__name__)


class UserRepository:
    """Data Access Object for User model operations."""

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        """
        Retrieve a user by their primary key.

        Args:
            user_id: The integer ID of the user.

        Returns:
            User instance if found, None otherwise.
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.debug(f"User with id={user_id} not found.")
            return None

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        """
        Retrieve a user by their email address (case-insensitive).

        Args:
            email: The email address to search for.

        Returns:
            User instance if found, None otherwise.
        """
        try:
            return User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None

    @staticmethod
    def create_user(email: str, password: str, name: str, phone: Optional[str] = None) -> User:
        """
        Create and persist a new user with a hashed password.

        Args:
            email:    Email address (must be unique).
            password: Plain-text password — will be hashed by set_password().
            name:     Full display name.
            phone:    Optional phone number.

        Returns:
            The newly created and saved User instance.
        """
        user = User(email=email, name=name, phone=phone, status='active')
        user.set_password(password)
        user.save()
        logger.info(f"Created user id={user.id} email={email}")
        return user

    @staticmethod
    def update_user(user: User, name: str, phone: Optional[str]) -> User:
        """
        Update mutable profile fields for an existing user.

        Args:
            user:  The User instance to update.
            name:  New display name.
            phone: New phone number (can be None to clear).

        Returns:
            The updated User instance.
        """
        user.name = name
        user.phone = phone
        user.save(update_fields=['name', 'phone'])
        logger.info(f"Updated profile for user id={user.id}")
        return user

    @staticmethod
    def get_all_active() -> QuerySet:
        """
        Return all users that are not banned.

        Returns:
            QuerySet of active users ordered by registration date.
        """
        return User.objects.filter(status='active').order_by('-created_at')


class MovieRepository:
    """Data Access Object for Movie model operations."""

    @staticmethod
    def get_all_active() -> QuerySet:
        """
        Return all movies currently showing or coming soon.

        Returns:
            QuerySet of movies with status 'now_showing' or 'coming_soon'.
        """
        return Movie.objects.filter(
            Q(status='now_showing') | Q(status='coming_soon')
        ).order_by('-release_date')

    @staticmethod
    def get_by_id(movie_id: int) -> Optional[Movie]:
        """
        Retrieve a single movie by its primary key.

        Args:
            movie_id: The integer ID of the movie.

        Returns:
            Movie instance if found, None otherwise.
        """
        try:
            return Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            logger.debug(f"Movie id={movie_id} not found.")
            return None

    @staticmethod
    def filter_movies(
        status: Optional[str] = None,
        genre: Optional[str] = None,
        format: Optional[str] = None,
        search_query: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> QuerySet:
        """
        Apply multiple optional filters to the movie catalog.

        Args:
            status:       Filter by status slug (e.g. 'now_showing', 'coming_soon').
            genre:        Case-insensitive substring match on genre field.
            format:       Case-insensitive substring match on formats field.
            search_query: Full-text search on title and description.
            sort_by:      Sort key — one of 'rating', 'newest', 'title'.
                          Defaults to newest release_date.

        Returns:
            Filtered and sorted QuerySet of Movie objects.
        """
        movies = Movie.objects.all()

        if status:
            movies = movies.filter(status=status)
        if genre:
            movies = movies.filter(genre__icontains=genre)
        if format:
            movies = movies.filter(formats__icontains=format)
        if search_query:
            movies = movies.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        sort_map = {
            'rating': '-rating',
            'newest': '-release_date',
            'title': 'title',
        }
        movies = movies.order_by(sort_map.get(sort_by, '-release_date'))
        return movies


class BookingRepository:
    """Data Access Object for Booking model operations."""

    @staticmethod
    def get_by_id(booking_id: int) -> Optional[Booking]:
        """
        Retrieve a single booking by its primary key.

        Args:
            booking_id: The integer ID of the booking.

        Returns:
            Booking instance with related data if found, None otherwise.
        """
        try:
            return Booking.objects.select_related(
                'user', 'showtime__movie', 'showtime__screen__theater'
            ).get(id=booking_id)
        except Booking.DoesNotExist:
            logger.debug(f"Booking id={booking_id} not found.")
            return None

    @staticmethod
    def get_user_bookings(user_id: int) -> QuerySet:
        """
        Return all bookings for a specific user, newest first.

        Args:
            user_id: The ID of the user whose bookings to fetch.

        Returns:
            QuerySet of Booking objects ordered by creation date descending.
        """
        return Booking.objects.filter(user_id=user_id).select_related(
            'showtime__movie', 'showtime__screen__theater'
        ).prefetch_related('items__seat').order_by('-created_at')

    @staticmethod
    def get_all_bookings() -> QuerySet:
        """
        Return all bookings in the system (for admin use).

        Returns:
            QuerySet of all Booking objects ordered by creation date descending.
        """
        return Booking.objects.all().select_related(
            'user', 'showtime__movie'
        ).order_by('-created_at')


class ShowtimeRepository:
    """Data Access Object for Showtime model operations."""

    @staticmethod
    def get_by_id(showtime_id: int) -> Optional[Showtime]:
        """
        Retrieve a single showtime by its primary key.

        Args:
            showtime_id: The integer ID of the showtime.

        Returns:
            Showtime instance with related movie and screen if found, None otherwise.
        """
        try:
            return Showtime.objects.select_related(
                'movie', 'screen__theater'
            ).get(id=showtime_id)
        except Showtime.DoesNotExist:
            logger.debug(f"Showtime id={showtime_id} not found.")
            return None

    @staticmethod
    def get_movie_showtimes(movie_id: int) -> QuerySet:
        """
        Return all future showtimes for a given movie.

        Args:
            movie_id: The ID of the movie to fetch showtimes for.

        Returns:
            QuerySet of upcoming Showtime objects ordered by start_time.
        """
        return Showtime.objects.filter(
            movie_id=movie_id
        ).select_related('screen__theater').order_by('start_time')


class DiscountRepository:
    """Data Access Object for Discount/Coupon model operations."""

    @staticmethod
    def get_by_code(code: str) -> Optional[Discount]:
        """
        Retrieve a discount coupon by its code string (case-insensitive).

        Args:
            code: The coupon code string (e.g. 'SUMMER2026').

        Returns:
            Discount instance if found, None if code does not exist.
        """
        try:
            return Discount.objects.get(code__iexact=code)
        except Discount.DoesNotExist:
            return None
