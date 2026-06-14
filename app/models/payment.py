from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, ForeignKey

from app.core.db import Base

class PaymentStatus(str, Enum):
    SUCCESS = "SUCCESS",
    PENDING = "PENDING",
    FAILED = "FAILED"

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    booking_id: Mapped[UUID] = mapped_column(ForeignKey("bookings.id"), index=True)

    idempotency_key: Mapped[str] = mapped_column(nullable=False, index=True)
    status: Mapped[PaymentStatus] = mapped_column(default=PaymentStatus.PENDING, index=True)
    card_token: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    booking: Mapped["Booking"] = relationship(back_populates="payments")
