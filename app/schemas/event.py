from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from decimal import Decimal
from uuid import UUID

class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    date: datetime
    total_tickets: int = Field(..., gt=0)
    ticket_price: Decimal = Field(max_digits=10, decimal_places=2, gt=0)

    @field_validator("ticket_price")
    @classmethod
    def round_price(cls, value):
        if isinstance(value, (float, int, str)):
            return Decimal(str(value)).quantize(Decimal("0.01"))
        return value

class EventResponse(BaseModel):
    title: str
    date: datetime
    total_tickets: int
    available_tickets: int
