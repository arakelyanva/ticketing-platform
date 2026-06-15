from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking, BookingStatus, Event


@pytest.mark.asyncio
async def test_models_and_hybrid_properties(db_session: AsyncSession):
    # 1. Populate an event with 10 total seats
    event = Event(
        title="Repository Test Show",
        total_tickets=10,
        ticket_price=Decimal("25.00")
    )
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    # HELD booking
    hold_booking = Booking(
        event_id=event.id,
        user_id=uuid4(),
        tickets_count=2,
        status=BookingStatus.HELD
    )
    # PAID booking
    paid_booking = Booking(
        event_id=event.id,
        user_id=uuid4(),
        tickets_count=3,
        status=BookingStatus.PAID
    )
    # CANCELED booking
    expired_booking = Booking(
        event_id=event.id,
        user_id=uuid4(),
        tickets_count=4,
        status=BookingStatus.CANCELED
    )

    db_session.add_all([hold_booking, paid_booking, expired_booking])
    await db_session.commit()
    await db_session.refresh(
        event,
        attribute_names=["bookings"]
    )

    # Calculate remaining capacity (10 - 2 - 3 = 5)
    assert event.available_tickets == 5
