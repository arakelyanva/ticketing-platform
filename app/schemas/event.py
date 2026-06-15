from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import BookingStatus


class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    total_tickets: int = Field(..., gt=0)
    ticket_price: Decimal = Field(max_digits=10, decimal_places=2, gt=0)

    @field_validator("ticket_price")
    @classmethod
    def round_price(cls, value):
        if isinstance(value, (float, int, str)):
            return Decimal(str(value)).quantize(Decimal("0.01"))
        return value

class EventBookings(BaseModel):
    id: UUID
    user_id: UUID
    tickets_count: int
    status: BookingStatus
    created_at: datetime
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EventResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    total_tickets: int
    available_tickets: int
    bookings: list[EventBookings] = []

    model_config = ConfigDict(from_attributes=True)
