import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.core.db import AsyncSessionLocal
from app.models import Event, Booking, BookingStatus, Payment, PaymentStatus

async def seed_database():
    async with AsyncSessionLocal() as session:
        # Check if database is already populated
        existing_events = await session.execute(select(Event).limit(1))
        if existing_events.scalars().first():
            print("Database already contains data. Skipping seeding.")
            return

        print("Seeding database records...")

        event1 = Event(
            title="Tech Conference 2026",
            total_tickets=200,
            ticket_price=Decimal("150.00")
        )
        event2 = Event(
            title="Indie Rock Concert",
            total_tickets=50,
            ticket_price=Decimal("45.50")
        )
        event3 = Event(
            title="Local Charity Gala",
            total_tickets=100,
            ticket_price=Decimal("75.00")
        )

        session.add_all([event1, event2, event3])
        await session.commit()
        await session.refresh(event1)
        await session.refresh(event2)

        user_alpha = uuid4()
        user_beta = uuid4()

        paid_booking = Booking(
            event_id=event1.id,
            user_id=user_alpha,
            tickets_count=1,
            status=BookingStatus.PAID
        )
        session.add(paid_booking)
        await session.commit()
        await session.refresh(paid_booking)

        success_payment = Payment(
            booking_id=paid_booking.id,
            idempotency_key=f"idmp_req_{uuid4().hex[:8]}",
            status=PaymentStatus.SUCCESS,
            card_token="tok_1234567890abcdef12345678",
            message="Payment captured"
        )
        session.add(success_payment)

        active_hold = Booking(
            event_id=event1.id,
            user_id=user_beta,
            tickets_count=1,
            status=BookingStatus.HELD
        )
        session.add(active_hold)

        failed_booking = Booking(
            event_id=event2.id,
            user_id=user_alpha,
            tickets_count=1,
            status=BookingStatus.CANCELED
        )
        session.add(failed_booking)
        await session.commit()
        await session.refresh(failed_booking)

        failed_payment = Payment(
            booking_id=failed_booking.id,
            idempotency_key=f"idmp_req_{uuid4().hex[:8]}",
            status=PaymentStatus.FAILED,
            card_token="tok_1213amaafsgddgadabcbcreb",
            message="Card declined: Insufficient funds"
        )
        session.add(failed_payment)

        await session.commit()
        print("Database successfully seeded with mock tracking data!")
        await session.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
