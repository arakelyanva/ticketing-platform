# app/api/routes.py
import json
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session, get_event_lock
from app.models.models import Event, Booking, BookingStatus, PaymentIdempotency
from app.models.schemas import EventCreate, EventResponse, BookingCreate, BookingResponse

router = APIRouter()

async def calculate_available_tickets(session: AsyncSession, event_id: UUID, total_capacity: int) -> int:
    # Sum up all active tickets held or paid for this event
    now = datetime.utcnow()
    query = select(Booking).where(
        Booking.event_id == event_id,
        ((Booking.status == BookingStatus.PAID) |
         ((Booking.status == BookingStatus.HELD) & (Booking.expires_at > now)))
    )
    result = await session.execute(query)
    active_bookings = result.scalars().all()
    allocated_tickets = sum(b.tickets_count for b in active_bookings)
    return max(0, total_capacity - allocated_tickets)


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(payload: EventCreate, session: AsyncSession = Depends(get_session)):
    new_event = Event(title=payload.title, total_capacity=payload.total_capacity)
    session.add(new_event)
    await session.commit()
    await session.refresh(new_event)
    return EventResponse(
        id=new_event.id,
        title=new_event.title,
        total_capacity=new_event.total_capacity,
        available_inventory=new_event.total_capacity
    )


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: UUID, session: AsyncSession = Depends(get_session)):
    event = await session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    available = await calculate_available_tickets(session, event.id, event.total_capacity)
    return EventResponse(
        id=event.id,
        title=event.title,
        total_capacity=event.total_capacity,
        available_inventory=available
    )


@router.post("/events/{event_id}/book", response_model=BookingResponse)
async def book_tickets(event_id: UUID, payload: BookingCreate, session: AsyncSession = Depends(get_session)):
    event = await session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Mutex lock per event ensures concurrent lookups/updates inside SQLite remain atomic
    lock = await get_event_lock(str(event_id))
    async with lock:
        available = await calculate_available_tickets(session, event.id, event.total_capacity)

        if available < payload.tickets_count:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail=f"Not enough tickets available. Requested: {payload.tickets_count}, Available: {available}"
            )

        new_booking = Booking(
            event_id=event.id,
            tickets_count=payload.tickets_count,
            status=BookingStatus.HELD,
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        session.add(new_booking)
        await session.commit()
        await session.refresh(new_booking)
        return new_booking


@router.post("/bookings/{booking_id}/pay")
async def process_payment(
    booking_id: UUID,
    idempotency_key: str = Header(None, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_session)
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Missing required 'Idempotency-Key' header")

    idem_record = await session.get(PaymentIdempotency, idempotency_key)
    if idem_record:
        # Return exact identical body cached from the previous execution safely
        return json.loads(idem_record.response_body)

    booking = await session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking record not found")

    if booking.status == BookingStatus.PAID:
        return {"status": "SUCCESS", "message": "Already processed and settled"}

    if booking.status == BookingStatus.CANCELED or booking.expires_at < datetime.utcnow():
        booking.status = BookingStatus.CANCELED
        await session.commit()
        raise HTTPException(status_code=400, detail="Cannot process payment: Hold expired or canceled")

    booking.status = BookingStatus.PAID
    session.add(booking)

    success_payload = {"status": "SUCCESS", "booking_id": str(booking.id), "message": "Payment captured"}
    new_idem = PaymentIdempotency(
        idempotency_key=idempotency_key,
        booking_id=booking.id,
        response_status=200,
        response_body=json.dumps(success_payload)
    )
    session.add(new_idem)
    await session.commit()

    return success_payload

