from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from datetime import datetime, timezone, timedelta

from app.core.db import get_event_lock
from app.models import Booking, BookingStatus
from app.schemas import EventCreate, EventResponse, BookingCreate, BookingResponse
from app.exceptions import EventNotFound, TicketsUnavailable

class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all() -> List[EventResponse]:
        return await self.session.scalars(select(Event)).all()

    async def create(payload: EventCreate) -> EventResponse:
        new_event = Event(payload)

        self.session.add(new_event)
        await self.session.commit()
        await self.session.refresh(new_event)

        return EventResponse(
            id=new_event.id,
            title=new_event.title,
            total_tickets=new_event.total_tickets,
            available_tickets=new_event.total_tickets
        )

    async def get_event(event_id: UUID) -> EventResponse:
        event = await self.session.get(Event, event_id)

        if not event:
            raise EventNotFound(event_id)

        return EventResponse(
            id=event.id,
            title=event.title,
            total_tickets=event.total_tickets,
            available_tickets=event.available_tickets
        )

    async def book_ticket(event_id: UUID, payload: BookingCreate) -> BookingResponse:
        event = await self.session.get(Event, event_id)

        if not event:
            raise EventNotFound(event_id)

        lock = await get_event_lock(str(event_id))

        async with lock:
            # We can only book a single ticket in a single request
            if event.available_tickets < 1:
                raise TicketsUnavailable(1, event.available_tickets)

            new_booking = Booking(
                event_id=event.id,
                tickets_count=1,
                status=BookingStatus.HELD,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
            )

            self.session.add(new_booking)

            await self.session.commit()
            await self.session.refresh(new_booking)

            return BookingResponse(booking_id=new_booking.id)
