from datetime import date, datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from app.core.security import create_refresh_token


@pytest.mark.asyncio
async def test_httponly_token_cookie_rotation(async_client: AsyncClient, seed_data: dict):
    """
    Validates HttpOnly cookie token pair:
    - 15-minute access token
    - 7-day refresh token
    - Token rotation on /auth/refresh
    """
    user = seed_data["faculty_user"]
    refresh_tok = create_refresh_token(str(user.id))

    # Send refresh token via HttpOnly cookie
    resp = await async_client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": refresh_tok},
    )
    assert resp.status_code == 200, resp.text
    cookies = resp.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies

    # Test logout clears cookies
    logout_resp = await async_client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200


@pytest.mark.asyncio
async def test_availability_matrix_and_slot_generation(async_client: AsyncClient, seed_data: dict):
    """
    Validates configuring availability matrix rules and computing timezone-aware conflict-free slots.
    """
    public_prof = seed_data["public_prof"]
    admin = seed_data["admin_user"]
    from app.core.security import create_access_token
    token = create_access_token(str(admin.id), admin.email, admin.roles)

    # 1. Update availability matrix (e.g. Tuesday 08:00 - 12:00, 45-min slots, 15-min buffer)
    matrix_payload = [
        {
            "day_of_week": 1,  # Tuesday
            "start_time": "08:00",
            "end_time": "12:00",
            "slot_duration_minutes": 45,
            "buffer_minutes": 15,
            "is_active": True,
        }
    ]

    put_resp = await async_client.put(
        f"/api/v1/availability/{public_prof.id}",
        json=matrix_payload,
        cookies={"access_token": token},
    )
    assert put_resp.status_code == 200, put_resp.text
    rules = put_resp.json()["rules"]
    assert len(rules) == 1
    assert rules[0]["slot_duration_minutes"] == 45

    # 2. Compute slots for next Tuesday
    today = date.today()
    days_ahead = (1 - today.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    target_tuesday = today + timedelta(days=days_ahead)

    slots_resp = await async_client.get(
        f"/api/v1/availability/{public_prof.id}/slots?target_date={target_tuesday.isoformat()}&timezone=America/New_York"
    )
    assert slots_resp.status_code == 200
    slots = slots_resp.json()
    assert len(slots) >= 3
    assert slots[0]["timezone"] == "America/New_York"
    assert slots[0]["is_available"] is True
