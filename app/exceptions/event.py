from uuid import UUID

from app.exceptions.base_exceptions import RepositoryException


class EventNotFound(RepositoryException):
    """Raised when an event does not exist in the database."""
    def __init__(self, event_id: UUID):
        super().__init__(f"Event with ID={event_id} was not found.")

class TicketsUnavailable(RepositoryException):
    def __init__(self, tickets_count: int, available: int):
        super().__init__(
            f"Not enough tickets available. Requested: {tickets_count}, Available: {available}"
        )

class InvalidUserId(RepositoryException):
    """Raised when user_id is not a valid UUID v4."""
    def __init__(self, user_id: UUID):
        super().__init__(f"user_id={user_id} is invalid. Only UUID version 4 identifiers are allowed.")
