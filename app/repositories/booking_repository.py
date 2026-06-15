import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from uuid import UUID
from datetime import datetime, timezone

from app.models import Booking, BookingStatus, Payment, PaymentStatus
from app.schemas import PaymentCreate, PaymentResponse
from app.exceptions import IdempotencyKeyMissing, BookingNotFound, BookingExpired, PaymentAlreadyExists

class BookingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def set_payment_status(self, payment_record: Payment, status: PaymentStatus):
        payment_record.status = status
        self.session.add(payment_record)

    async def process_payment(
        self,
        booking_id: UUID,
        idempotency_key: str,
        payload: PaymentCreate
    ) -> PaymentResponse:
        if not idempotency_key:
            raise IdempotencyKeyMissing

        query = (
            select(Payment)
            .where(Payment.idempotency_key == idempotency_key)
            .options(selectinload(Payment.booking))
        )

        result = await self.session.scalars(query)
        payment_record = result.first()

        if payment_record and payment_record.status != PaymentStatus.PENDING:
            raise PaymentAlreadyExists(payment_record.status)

        booking = await self.session.get(Booking, booking_id)
        if not booking:
            raise BookingNotFound(booking_id)

        if booking.status == BookingStatus.PAID:
            if payment_record:
                self.set_payment_status(payment_record, PaymentStatus.SUCCESS)
                await self.session.commit()

            return PaymentResponse(
                status=PaymentStatus.SUCCESS,
                booking=booking,
                message="Already processed and settled"
            )

        expired_utc = booking.expires_at.replace(tzinfo=timezone.utc)
        time_now_utc = datetime.now(timezone.utc)
        if booking.status == BookingStatus.CANCELED or expired_utc < time_now_utc:
            booking.status = BookingStatus.CANCELED
            if payment_record:
               self.set_payment_status(payment_record, PaymentStatus.FAILED)

            await self.session.commit()
            raise BookingExpired

        # Lets assume here goes actual payment gateway operations -->
        # ...
        # <--

        booking.status = BookingStatus.PAID
        self.session.add(booking)

        response = PaymentResponse(
            status=PaymentStatus.SUCCESS,
            booking=booking,
            message="Payment captured"
        )

        if payment_record:
            payment_record.card_token = payload.card_token
            payment_record.message = response.message
            self.set_payment_status(payment_record, response.status)
        else:
            new_payment = Payment(
                idempotency_key=idempotency_key,
                booking_id=response.booking.id,
                card_token=payload.card_token,
                status=response.status,
                message=response.message
            )
            self.session.add(new_payment)

        await self.session.commit()

        return response
