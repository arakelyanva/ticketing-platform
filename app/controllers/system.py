from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session

router = APIRouter(tags=["System"])

@router.api_route("/health", methods=["GET", "HEAD"])
async def health_check(
    session: AsyncSession = Depends(get_session)
):
    """Health check endpoint for Docker container monitoring."""
    try:
        # Check DB connection
        await session.execute(select(1))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Infrastructure degraded: {str(e)}")
