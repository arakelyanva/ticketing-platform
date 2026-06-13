from pydantic import BaseModel, Field
from uuid import UUID

from app.models import BookingStatus

class PaymentCreate(BaseModel):
    # Random requirements, since card_token is mocked
    card_token: str = Field(..., min_length=8, max_length=32)

class PaymentResponse(BaseModel):
    booking_id: UUID
    status: BookingStatus
    message: str
