import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_optional_current_user
from app.core.exceptions import DoubleBookingException, NodeNotFoundException
from app.database import get_db
from app.models.appointment import Appointment
from app.models.booking_intent import BookingIntent, IntentStatus
from app.models.node import Node, VisibilityTier
from app.models.user import User
from app.schemas.booking import (
    AppointmentResponse,
    BookingIntentResponse,
    BookingIntentSubmit,
    SlotBookingRequest,
    TriageActionRequest,
)
from app.services.intent_router import IntentRouter
from app.services.scheduling_service import SchedulingService
from app.services.visibility_evaluator import VisibilityEvaluator

router = APIRouter(prefix="/booking", tags=["Scheduling, Concurrency & Intent Triage"])


@router.post("/book", response_model=AppointmentResponse)
async def book_appointment(
    payload: SlotBookingRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Direct slot booking with PostgreSQL 'SELECT ... FOR UPDATE' concurrency locking.
    If the target node is HIDDEN or requires triage, this endpoint rejects direct booking
    unless a valid escalation token is provided.
    """
    node = await session.get(Node, payload.resource_node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Resource node not found.")

    # Guardrail: Check if node requires triage pipeline
    if VisibilityEvaluator.requires_intent_triage(node):
        if not payload.escalation_token:
            triage_id = VisibilityEvaluator.get_triage_project_id(node) or str(node.parent_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "DIRECT_BOOKING_FORBIDDEN",
                    "message": "This resource is protected. Submit a booking intent for triage review.",
                    "triage_project_id": triage_id,
                },
            )

    try:
        appt = await SchedulingService.book_slot_atomic(
            session=session,
            resource_node_id=payload.resource_node_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            booker_name=payload.booker_name,
            booker_email=payload.booker_email,
            title=payload.title,
            notes=payload.notes,
            booker_user_id=current_user.id if current_user else None,
        )
        await session.commit()
        return AppointmentResponse.model_validate(appt)
    except DoubleBookingException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/intent/submit", response_model=BookingIntentResponse)
async def submit_booking_intent(
    payload: BookingIntentSubmit,
    session: AsyncSession = Depends(get_db),
):
    """
    Submits a booking request through the indirect Intent Pipeline.
    Used for screening executive or protected nodes.
    """
    intent = await IntentRouter.submit_booking_intent(
        session=session,
        target_node_id=payload.target_node_id,
        booker_name=payload.booker_name,
        booker_email=payload.booker_email,
        requested_start=payload.requested_start_time,
        requested_end=payload.requested_end_time,
        intake_responses=payload.intake_responses,
        intent_note=payload.intent_note,
    )
    await session.commit()
    return BookingIntentResponse.model_validate(intent)


@router.get("/intent/queue", response_model=List[BookingIntentResponse])
async def list_triage_queue(
    status_filter: Optional[IntentStatus] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Screening triage interface for intake officers or executive assistants to review incoming intents.
    """
    stmt = select(BookingIntent)
    if status_filter:
        stmt = stmt.where(BookingIntent.status == status_filter)
    stmt = stmt.order_by(BookingIntent.created_at.desc())

    res = await session.execute(stmt)
    intents = res.scalars().all()
    return [BookingIntentResponse.model_validate(i) for i in intents]


@router.post("/intent/{intent_id}/triage", response_model=BookingIntentResponse)
async def execute_triage(
    intent_id: uuid.UUID,
    payload: TriageActionRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Evaluates booking intent. If action is 'approve_and_escalate', generates
    a signed escalation token linking to the executive node.
    """
    intent = await IntentRouter.execute_triage_action(
        session=session,
        intent_id=intent_id,
        action=payload.action,
        reviewer_notes=payload.reviewer_notes,
        escalate_to_node_id=payload.escalate_to_node_id,
    )
    await session.commit()
    return BookingIntentResponse.model_validate(intent)


@router.post("/intent/{intent_id}/confirm", response_model=AppointmentResponse)
async def confirm_escalated_booking(
    intent_id: uuid.UUID,
    escalation_token: str,
    session: AsyncSession = Depends(get_db),
):
    """
    Finalizes the appointment by validating the cryptographic escalation token.
    Uses SELECT FOR UPDATE row locking.
    """
    appt = await IntentRouter.confirm_escalated_booking(
        session=session,
        intent_id=intent_id,
        escalation_token=escalation_token,
    )
    await session.commit()
    return AppointmentResponse.model_validate(appt)


@router.get("/appointments/my", response_model=List[AppointmentResponse])
async def get_my_appointments(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Retrieves appointments either booked by the user or hosted on one of the user's mapped resource nodes.
    """
    stmt = select(Appointment).where(
        or_(
            Appointment.booker_user_id == current_user.id,
            Appointment.booker_email == current_user.email,
        )
    ).order_by(Appointment.start_time.asc())
    res = await session.execute(stmt)
    appts = res.scalars().all()
    return [AppointmentResponse.model_validate(a) for a in appts]
