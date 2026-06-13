import os
import asyncio
from typing import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection wrapper to get the active SQLite Session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

DB_LOCKS = {}
db_locks_mutex = asyncio.Lock()

async def get_event_lock(event_id: str) -> asyncio.Lock:
    async with db_locks_mutex:
        if event_id not in DB_LOCKS:
            DB_LOCKS[event_id] = asyncio.Lock()
        return DB_LOCKS[event_id]

