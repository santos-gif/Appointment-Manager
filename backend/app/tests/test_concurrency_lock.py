import asyncio
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_concurrency_double_booking_lock(async_client: AsyncClient, seed_data: dict):
    """
    Simulates high-concurrency race condition:
    Multiple simultaneous booking requests for the exact same resource timeslot.
    Asserts that exactly one succeeds (200) and all competing requests are rejected (409 Conflict).
    """
    public_prof = seed_data["public_prof"]
    start_time = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=2, hours=10)
    end_time = start_time + timedelta(minutes=30)

    payload_template = {
        "resource_node_id": str(public_prof.id),
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "title": "Quantum Algorithm Consult",
    }

    async def attempt_booking(idx: int):
        body = {
            **payload_template,
            "booker_name": f"Booker Competitor {idx}",
            "booker_email": f"booker{idx}@example.com",
        }
        return await async_client.post("/api/v1/booking/book", json=body)

    # Launch 10 simultaneous booking attempts
    responses = await asyncio.gather(*[attempt_booking(i) for i in range(10)])

    success_responses = [r for r in responses if r.status_code == 200]
    conflict_responses = [r for r in responses if r.status_code == 409]

    # Exactly one request must win the slot
    assert len(success_responses) == 1, f"Expected 1 winner, got {len(success_responses)}"
    assert len(conflict_responses) == 9, f"Expected 9 conflicts, got {len(conflict_responses)}"

    winner_data = success_responses[0].json()
    assert winner_data["resource_node_id"] == str(public_prof.id)
    assert winner_data["status"] == "CONFIRMED"
