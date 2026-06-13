from datetime import datetime, timezone
from typing import List
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Numeric, DateTime, func, select
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.db import Base
from app.models.booking import Booking, BookingStatus

class Event(Base):
    __tablename__ = "events"

    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    title: Mapped[str] = mapped_column(String, index=True)
    total_tickets: Mapped[int] = mapped_column(Integer)
    ticket_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2, asdecimal=True),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )
    bookings: Mapped[List["Booking"]] = relationship(back_populates="event")

    @hybrid_property
    @classmethod
    def available_tickets(self) -> int:
        return self.total_tickets - sum(
            booking.tickets_count
            for booking in self.bookings
            if booking.status in (BookingStatus.HELD, BookingStatus.PAID)
        )

    @available_tickets.inplace.expression
    @classmethod
    def _available_tickets_expression(cls):
        return cls.total_tickets - (
            select(func.coalesce(func.sum(Booking.tickets_count), 0))
            .where(
                Booking.event_id == cls.id,
                Booking.status.in_([BookingStatus.HELD, BookingStatus.PAID])
            )
            .correlate(cls)
            .scalar_subquery()
        )
