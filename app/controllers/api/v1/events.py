from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session

from app.schemas import EventCreate, EventResponse, BookingCreate, BookingResponse
from app.repositories import EventRepository
from app.exceptions import EventNotFound, TicketsUnavailable, InvalidUserId

async def catch_router_errors():
    try:
        yield
    except InvalidUserId as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except EventNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except TicketsUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

router = APIRouter(
    prefix="/events",
    tags=["Events"],
    dependencies=[Depends(catch_router_errors)]
)

async def get_event_repository(session: AsyncSession = Depends(get_session)) -> EventRepository:
    return EventRepository(session)

@router.get("/", response_model=List[EventResponse], status_code=status.HTTP_200_OK)
async def get_all_events(repo: EventRepository = Depends(get_event_repository)):
    return await repo.get_all()

@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(payload: EventCreate, repo: EventRepository = Depends(get_event_repository)):
    return await repo.create(payload)


@router.get("/{event_id}", response_model=EventResponse, status_code=status.HTTP_200_OK)
async def get_event(event_id: UUID, repo: EventRepository = Depends(get_event_repository)):
    return await repo.get_event(event_id)


@router.post("/{event_id}/book", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def book_ticket(event_id: UUID, payload: BookingCreate, repo: EventRepository = Depends(get_event_repository)):
    return await repo.book_ticket(event_id, payload)
