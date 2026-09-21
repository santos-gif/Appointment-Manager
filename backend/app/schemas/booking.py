import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.appointment import AppointmentStatus
from app.models.booking_intent import IntentStatus


class AvailableSlot(BaseModel):
    slot_start: datetime
    slot_end: datetime
    formatted_start: str
    formatted_end: str
    timezone: str
    is_available: bool


class SlotBookingRequest(BaseModel):
    resource_node_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    booker_name: str
    booker_email: EmailStr
    title: str = "Scheduled Appointment"
    notes: Optional[str] = None
    escalation_token: Optional[str] = Field(None, description="Required when booking against a HIDDEN or protected node")
    payment_reference: Optional[str] = None


class BookingIntentSubmit(BaseModel):
    target_node_id: uuid.UUID
    requested_start_time: datetime
    requested_end_time: datetime
    booker_name: str
    booker_email: EmailStr
    intake_responses: Dict[str, Any] = Field(default_factory=dict)
    intent_note: Optional[str] = None


class TriageActionRequest(BaseModel):
    action: str = Field(description="'approve_and_escalate', 'approve', 'reject', 'reschedule'")
    escalate_to_node_id: Optional[uuid.UUID] = None
    reviewer_notes: Optional[str] = None
    rescheduled_start_time: Optional[datetime] = None
    rescheduled_end_time: Optional[datetime] = None


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    resource_node_id: uuid.UUID
    booker_name: str
    booker_email: str
    title: str
    notes: Optional[str]
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus
    payment_status: str
    payment_amount_cents: int
    created_at: datetime


class BookingIntentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    target_node_id: uuid.UUID
    triage_project_id: Optional[uuid.UUID]
    escalated_node_id: Optional[uuid.UUID]
    booker_name: str
    booker_email: str
    requested_start_time: datetime
    requested_end_time: datetime
    status: IntentStatus
    intake_responses: Dict[str, Any]
    triage_notes: Optional[str]
    escalation_token: Optional[str]
    created_at: datetime
    updated_at: datetime
