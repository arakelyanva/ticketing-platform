from fastapi import APIRouter, Header, Depends, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session

from app.schemas import PaymentCreate, PaymentResponse
from app.repositories import BookingRepository
from app.exceptions import IdempotencyKeyMissing, BookingNotFound, BookingExpired

async def catch_router_errors():
    try:
        yield
    except IdempotencyKeyMissing as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except BookingNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except BookingExpired as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

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
    idempotency_key: str = Header(None, alias="Idempotency-Key"),
    payload=PaymentCreate,
    repo: BookingRepository = Depends(get_booking_repository)
):
    return await repo.process_payment(idempotency_key, payload)
