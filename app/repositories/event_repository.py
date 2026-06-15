from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_event_lock
from app.exceptions import EventNotFound, TicketsUnavailable
from app.models import Booking, BookingStatus, Event
from app.schemas import BookingCreate, BookingResponse, EventCreate, EventResponse


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[EventResponse]:
        query = (select(Event).options(selectinload(Event.bookings)))

        return (await self.session.scalars(query)).all()

    async def create(self, payload: EventCreate) -> EventResponse:
        new_event = Event(
            title=payload.title,
            total_tickets=payload.total_tickets,
            ticket_price=payload.ticket_price
        )

        self.session.add(new_event)
        await self.session.commit()
        await self.session.refresh(
            new_event,
            attribute_names=["bookings"]
        )

        return new_event

    async def get_event(self, event_id: UUID) -> EventResponse:
        event = await self.session.get(
            Event,
            event_id,
            options=[selectinload(Event.bookings)]
        )

        if not event:
            raise EventNotFound(event_id)

        return event

    async def book_ticket(self, event_id: UUID, payload: BookingCreate) -> BookingResponse:
        lock = await get_event_lock(str(event_id))

        async with lock:
            event = await self.session.get(
                Event,
                event_id,
                options=[selectinload(Event.bookings)],
                populate_existing=True # Clears cache inline
            )

            if not event:
                raise EventNotFound(event_id)

            # We can only book a single ticket in a single request
            if event.available_tickets < 1:
                raise TicketsUnavailable(1, event.available_tickets)

            new_booking = Booking(
                event_id=event.id,
                user_id=payload.user_id,
                tickets_count=1,
                status=BookingStatus.HELD,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
            )

            self.session.add(new_booking)

            await self.session.commit()
            await self.session.refresh(new_booking)

            return BookingResponse(booking_id=new_booking.id)
