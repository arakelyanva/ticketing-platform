import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.db import engine
from app.controllers.api.v1 import api_v1_router
from app.controllers.system import router as system_router
from app.workers.bookings_worker import cleanup_expired_holds

@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = asyncio.create_task(cleanup_expired_holds())

    yield

    engine.dispose()
    worker_task.cancel()
    await asyncio.gather(worker_task, return_exceptions=True)

app = FastAPI(title="Ticketing Platform", lifespan=lifespan)

app.include_router(system_router)
app.include_router(api_v1_router)
