from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from app.models import BookingStatus
from app.exceptions import InvalidUserId

class BookingCreate(BaseModel):
    user_id: UUID = Field(...)

    @field_validator("user_id")
    @classmethod
    def ensure_uuid_v4(cls, value: UUID) -> UUID:
        if value.version != 4:
            raise InvalidUserId(value)
        return value

class BookingResponse(BaseModel):
    booking_id: UUID
