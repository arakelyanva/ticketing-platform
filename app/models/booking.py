from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


# custom Enum class for handling BookingStatus states
class BookingStatus(str, Enum):
    HELD = "HELD"
    PAID = "PAID"
    CANCELED = "CANCELED"

class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)

    tickets_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[BookingStatus] = mapped_column(default=BookingStatus.HELD, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + timedelta(minutes=15)
    )

    event: Mapped["Event"] = relationship(back_populates="bookings")
    payments: Mapped["Payment"] = relationship(back_populates="booking")
