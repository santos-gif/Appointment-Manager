from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_intent_screening_and_escalation_lifecycle(async_client: AsyncClient, seed_data: dict):
    """
    Validates the indirect Intent-Based Routing Guardrail:
    1. Direct booking against HIDDEN / Protected node is blocked.
    2. Intent submission is routed to the triage project node.
    3. Reviewer approves & programmatically escalates with signed cryptographic token.
    4. Appointment is confirmed with the escalation token.
    """
    hidden_dean = seed_data["hidden_dean"]
    admin = seed_data["admin_user"]
    admin_token = create_access_token(str(admin.id), admin.email, admin.roles)

    start_time = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=3, hours=14)
    end_time = start_time + timedelta(minutes=45)

    # 1. Attempt direct booking against hidden executive node -> Must be blocked (403)
    direct_body = {
        "resource_node_id": str(hidden_dean.id),
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "booker_name": "External Partner",
        "booker_email": "partner@venturecapital.com",
    }
    direct_resp = await async_client.post("/api/v1/booking/book", json=direct_body)
    assert direct_resp.status_code == 403, direct_resp.text
    err_json = direct_resp.json()
    assert "triage_project_id" in err_json["detail"]

    # 2. Submit booking intent for triage review
    intent_body = {
        "target_node_id": str(hidden_dean.id),
        "requested_start_time": start_time.isoformat(),
        "requested_end_time": end_time.isoformat(),
        "booker_name": "External Partner",
        "booker_email": "partner@venturecapital.com",
        "intake_responses": {
            "purpose": "Endowment Grant Partnership",
            "organization": "Venture Fund LP",
            "tier": "Strategic",
        },
        "intent_note": "Requesting 45-minute confidential discussion regarding Dean endowment.",
    }
    submit_resp = await async_client.post("/api/v1/booking/intent/submit", json=intent_body)
    assert submit_resp.status_code == 200, submit_resp.text
    intent_data = submit_resp.json()
    intent_id = intent_data["id"]
    assert intent_data["status"] == "PENDING_REVIEW"

    # 3. Triage officer inspects queue and executes 'approve_and_escalate'
    triage_body = {
        "action": "approve_and_escalate",
        "reviewer_notes": "Strategic grant opportunity validated. Escalated directly to Dean calendar.",
    }
    triage_resp = await async_client.post(
        f"/api/v1/booking/intent/{intent_id}/triage",
        json=triage_body,
        cookies={"access_token": admin_token},
    )
    assert triage_resp.status_code == 200
    escalated_data = triage_resp.json()
    assert escalated_data["status"] == "APPROVED"
    assert escalated_data["escalation_token"] is not None
    escalation_token = escalated_data["escalation_token"]

    # 4. Booker confirms appointment using the escalation token
    confirm_resp = await async_client.post(
        f"/api/v1/booking/intent/{intent_id}/confirm?escalation_token={escalation_token}",
    )
    assert confirm_resp.status_code == 200, confirm_resp.text
    appt_data = confirm_resp.json()
    assert appt_data["status"] == "CONFIRMED"
    assert appt_data["resource_node_id"] == str(hidden_dean.id)

    # 5. Token reuse attempt should fail
    reuse_resp = await async_client.post(
        f"/api/v1/booking/intent/{intent_id}/confirm?escalation_token={escalation_token}",
    )
    assert reuse_resp.status_code == 400
