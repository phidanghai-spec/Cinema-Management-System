class CinemaException(Exception):
    """Base exception for all cinema business rule violations."""
    pass

class CineVerseException(CinemaException):
    """Base exception for CineVerse application errors."""
    pass

class UserNotFoundException(CinemaException):
    """Raised when a referenced user does not exist."""
    pass

class DuplicateEmailException(CinemaException):
    """Raised when registering with an already-used email address."""
    pass

class AccountBannedException(CinemaException):
    """Raised when a banned user attempts to log in or book."""
    pass

class InvalidCredentialsException(CinemaException):
    """Raised on login failure due to wrong email or password."""
    pass

class MovieNotFoundException(CinemaException):
    """Raised when a referenced movie does not exist."""
    pass

class ShowtimeNotFoundException(CinemaException):
    """Raised when a referenced showtime does not exist."""
    pass

class SeatNotFoundException(CinemaException):
    """Raised when one or more requested seats cannot be found."""
    pass

class BookingNotFoundException(CinemaException):
    """Raised when a referenced booking does not exist."""
    pass

class UnauthorizedActionException(CinemaException):
    """Raised when a user attempts an action on another user's resource."""
    pass

class InvalidTicketException(CinemaException):
    """Raised when a QR ticket code is malformed or not found."""
    pass

class SeatAlreadyBookedException(CineVerseException):
    """Raised when a user attempts to book a seat that has already been locked or booked by someone else."""
    pass

class InsufficientPointsException(CineVerseException):
    """Raised when a user attempts to redeem more loyalty points than they possess."""
    pass

class DiscountNotApplicableException(CineVerseException):
    """Raised when a discount coupon is invalid or not applicable for the current user/booking."""
    pass

class PaymentTimeoutException(CineVerseException):
    """Raised when a payment operation times out."""
    pass

class InvalidStateTransitionException(CineVerseException):
    """Raised when an invalid state transition is requested on a Booking."""
    pass
