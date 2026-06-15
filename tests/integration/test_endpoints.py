from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_event_lifecycle_and_idempotent_payment_matrix(client: AsyncClient, db_session: AsyncSession):
    # Step 1: Verify event creation returns 210/201 schema
    event_payload = {
        "title": "Idempotency Festival",
        "total_tickets": 100,
        "ticket_price": "50.00"
    }
    response = await client.post("/api/v1/events/", json=event_payload)
    assert response.status_code == 201
    event_id = response.json()["id"]

    # Step 2: Book a single seat
    booking_payload = {"user_id": str(uuid4())}
    b_response = await client.post(f"/api/v1/events/{event_id}/book", json=booking_payload)
    assert b_response.status_code == 201
    booking_id = b_response.json()["booking_id"]

    # Step 3: Run primary payment (Expect 211 / 201 Created)
    idem_key = f"idem_req{uuid4().hex[:8]}"
    pay_payload = {"card_token": "tok_12319237183"}
    headers = {"Idempotency-Key": idem_key}

    pay_response1 = await client.post(f"/api/v1/bookings/{booking_id}/pay", json=pay_payload, headers=headers)
    assert pay_response1.status_code == 201
    assert pay_response1.json()["status"] == "SUCCESS"

    # Step 4: Re-fire the same payment (Expect 409 Conflict on already PAID booking)
    pay_response2 = await client.post(f"/api/v1/bookings/{booking_id}/pay", json=pay_payload, headers=headers)
    assert pay_response2.status_code == 409
    assert pay_response2.json()["detail"] == "Payment with given Idempotency-Key and status=SUCCESS already exists."
