from uuid import UUID

from app.exceptions.base_exceptions import RepositoryException
from app.models import PaymentStatus


class IdempotencyKeyMissing(RepositoryException):
    """Raised when 'Idempotency-Key' header is missing."""
    def __init__(self):
        super().__init__("Missing required 'Idempotency-Key' header.")

class BookingNotFound(RepositoryException):
    """Raised when an event does not exist in the database."""
    def __init__(self, booking_id: UUID):
        super().__init__(f"Booking with ID={booking_id} was not found.")

class BookingExpired(RepositoryException):
    """Raised when the booking is already expired."""
    def __init__(self):
        super().__init__("Cannot process payment: Hold expired or canceled.")

class PaymentAlreadyExists(RepositoryException):
    """Raised when the booking is already expired."""
    def __init__(self, status: PaymentStatus):
        super().__init__(f"Payment with given Idempotency-Key and status={status} already exists.")
