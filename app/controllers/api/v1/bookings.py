from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.exceptions import (
    BookingExpired,
    BookingNotFound,
    IdempotencyKeyMissing,
    PaymentAlreadyExists,
)
from app.repositories import BookingRepository
from app.schemas import PaymentCreate, PaymentResponse


async def catch_router_errors():
    try:
        yield
    except IdempotencyKeyMissing as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except BookingNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (BookingExpired, PaymentAlreadyExists) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"],
    dependencies=[Depends(catch_router_errors)]
)

async def get_booking_repository(session: AsyncSession = Depends(get_session)) -> BookingRepository:
    return BookingRepository(session)

@router.post("/{booking_id}/pay", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def process_payment(
    booking_id: UUID,
    payload: PaymentCreate,
    idempotency_key: str = Header(None, alias="Idempotency-Key"),
    repo: BookingRepository = Depends(get_booking_repository)
):
    return await repo.process_payment(booking_id, idempotency_key, payload)
