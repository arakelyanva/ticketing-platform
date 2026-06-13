import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID
from datetime import datetime, timezone

from app.models import Booking, BookingStatus, Payment, PaymentStatus
from app.schemas import PaymentCreate, PaymentResponse
from app.exceptions import IdempotencyKeyMissing, BookingNotFound, BookingExpired

class BookingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def process_payment(idempotency_key: str, payload: PaymentCreate) -> PaymentResponse:
        if not idempotency_key:
            raise IdempotencyKeyMissing

        payment_record = await session.get(Payment, idempotency_key)
        if payment_record:
            return PaymentResponse(
                status=payment_record.status,
                booking_id=payment_record.booking_id,
                message=payment_record.message
            )

        booking = await session.get(Booking, booking_id)
        if not booking:
            raise BookingNotFound

        if booking.status == BookingStatus.PAID:
            return PaymentResponse(
                status=PaymentStatus.SUCCESS,
                booking_id=booking.id,
                message="Already processed and settled"
            )

        if booking.status == BookingStatus.CANCELED or booking.expires_at < datetime.now(timezone.utc):
            booking.status = BookingStatus.CANCELED
            await session.commit()
            raise BookingExpired

        # Lets assume here goes actual payment gateway operations -->
        # ...
        # <--

        booking.status = BookingStatus.PAID
        session.add(booking)

        response = PaymentResponse(
            status=PaymentStatus.SUCCESS,
            booking_id=booking.id,
            message="Payment captured"
        )

        new_payment = Payment(
            idempotency_key=idempotency_key,
            booking_id=response.booking_id,
            card_token=payload.card_token,
            status=response.status,
            message=response.message
        )

        session.add(new_payment)
        await session.commit()

        return response
