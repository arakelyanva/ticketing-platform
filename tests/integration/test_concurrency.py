import asyncio
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event


@pytest.mark.asyncio
async def test_high_demand_concurrency_prevents_overbooking(client: AsyncClient, db_session: AsyncSession):
    # 1. Create a high-demand event containing exactly 1 ticket left
    event = Event(
        title="Highly Demanded Finale",
        total_tickets=1,
        ticket_price=Decimal("500.00")
    )
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(
        event,
        attribute_names=["bookings"]
    )

    # 2. Simulate 50 simultaneous user requests trying to secure the 1 ticket
    request_count = 50
    payloads = [{"user_id": str(uuid4())} for _ in range(request_count)]

    # Fire all 50 asynchronous POST calls in parallel
    tasks = [
        client.post(f"/api/v1/events/{event.id}/book", json=payloads[i])
        for i in range(request_count)
    ]
    responses = await asyncio.gather(*tasks)

    # 3. Process outcomes
    success_responses = [r for r in responses if r.status_code == 201]
    conflict_responses = [r for r in responses if r.status_code == 409]

    # Verify that exactly 1 user succeeded and the remaining 49 were rejected with a Conflict status code
    assert len(success_responses) == 1
    assert len(conflict_responses) == 49

    # Verify the failure message matches your API design
    assert "Not enough tickets available" in conflict_responses[0].json()["detail"]
