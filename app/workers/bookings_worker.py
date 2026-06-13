import asyncio
from sqlalchemy import update

from app.core.db import AsyncSessionLocal
from app.models import Booking, BookingStatus

async def cleanup_expired_holds():
    """Background worker that releases unpaid holds after 15 minutes."""
    while True:
        try:
            await asyncio.sleep(60)

            async with AsyncSessionLocal() as session:
                now = datetime.utcnow()

                statement = (
                    update(Booking)
                    .where(Booking.status == BookingStatus.HELD, Booking.expires_at < now)
                    .values(status=BookingStatus.CANCELED)
                )
                await session.execute(statement)
                await session.commit()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[WORKER ERROR] Error executing `cleanup_expired_holds` worker: {e}")

