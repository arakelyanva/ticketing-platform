from fastapi import APIRouter

from app.controllers.api.v1 import bookings, events

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(events.router)
api_v1_router.include_router(bookings.router)
