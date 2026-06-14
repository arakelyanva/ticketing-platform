from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from app.models import BookingStatus, PaymentStatus

class PaymentBooking(BaseModel):
    id: UUID
    user_id: UUID
    tickets_count: int
    status: BookingStatus

    model_config = ConfigDict(from_attributes=True)

class PaymentCreate(BaseModel):
    # Random requirements, since card_token is mocked
    card_token: str = Field(..., min_length=8, max_length=32)

class PaymentResponse(BaseModel):
    status: PaymentStatus
    message: str
    booking: PaymentBooking

    model_config = ConfigDict(from_attributes=True)
