import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DomainException, NodeNotFoundException
from app.core.security import create_escalation_token, decode_jwt_token
from app.models.appointment import Appointment
from app.models.booking_intent import BookingIntent, IntentStatus
from app.models.node import Node, VisibilityTier
from app.services.scheduling_service import SchedulingService
from app.services.visibility_evaluator import VisibilityEvaluator


class IntentRouter:
    """
    Implements Intent-Based Routing Guardrails.
    Routes public/unauthorized requests through an indirect screening pipeline before
    escalating upward to protected or hidden executive nodes.
    """

    @staticmethod
    async def submit_booking_intent(
        session: AsyncSession,
        target_node_id: uuid.UUID,
        booker_name: str,
        booker_email: str,
        requested_start: datetime,
        requested_end: datetime,
        intake_responses: Dict[str, Any],
        intent_note: Optional[str] = None,
    ) -> BookingIntent:
        node = await session.get(Node, target_node_id)
        if not node:
            raise NodeNotFoundException(str(target_node_id))

        # Check if node has a designated triage project node
        triage_id_str = VisibilityEvaluator.get_triage_project_id(node)
        triage_project_id = uuid.UUID(triage_id_str) if triage_id_str else node.parent_id

        intent = BookingIntent(
            id=uuid.uuid4(),
            tenant_id=node.tenant_id,
            target_node_id=target_node_id,
            triage_project_id=triage_project_id,
            booker_name=booker_name,
            booker_email=booker_email,
            requested_start_time=requested_start,
            requested_end_time=requested_end,
            status=IntentStatus.PENDING_REVIEW,
            intake_responses=intake_responses,
            triage_notes=intent_note,
        )
        session.add(intent)
        await session.flush()
        return intent

    @staticmethod
    async def execute_triage_action(
        session: AsyncSession,
        intent_id: uuid.UUID,
        action: str,  # 'approve_and_escalate', 'reject', 'reschedule'
        reviewer_notes: Optional[str] = None,
        escalate_to_node_id: Optional[uuid.UUID] = None,
    ) -> BookingIntent:
        stmt = select(BookingIntent).where(BookingIntent.id == intent_id)
        res = await session.execute(stmt)
        intent = res.scalar_one_or_none()
        if not intent:
            raise DomainException(f"Booking intent {intent_id} was not found.")

        intent.triage_notes = reviewer_notes

        if action == "approve_and_escalate":
            intent.status = IntentStatus.APPROVED
            escalated_target = escalate_to_node_id or intent.target_node_id
            intent.escalated_node_id = escalated_target

            # Generate cryptographically signed single-use escalation token
            escalation_token = create_escalation_token(
                intent_id=str(intent.id),
                target_resource_id=str(escalated_target),
                minutes=120,  # 2 hours validity to confirm appointment
            )
            intent.escalation_token = escalation_token

        elif action == "reject":
            intent.status = IntentStatus.REJECTED

        elif action == "reschedule":
            intent.status = IntentStatus.RESCHEDULED

        await session.flush()
        return intent

    @staticmethod
    async def confirm_escalated_booking(
        session: AsyncSession,
        intent_id: uuid.UUID,
        escalation_token: str,
    ) -> Appointment:
        """
        Consumes the cryptographic escalation token and reserves the slot atomically.
        """
        # Validate escalation token
        try:
            payload = decode_jwt_token(escalation_token)
            if payload.get("token_type") != "escalation":
                raise DomainException("Invalid token type for escalation.")
            if payload.get("intent_id") != str(intent_id):
                raise DomainException("Escalation token mismatch for intent.")
        except Exception as e:
            raise DomainException(f"Invalid or expired escalation token: {str(e)}")

        stmt = select(BookingIntent).where(BookingIntent.id == intent_id)
        res = await session.execute(stmt)
        intent = res.scalar_one_or_none()
        if not intent or intent.status != IntentStatus.APPROVED:
            raise DomainException("Intent is not in approved state for booking.")

        target_resource = intent.escalated_node_id or intent.target_node_id

        # Atomic booking with SELECT FOR UPDATE concurrency lock
        appointment = await SchedulingService.book_slot_atomic(
            session=session,
            resource_node_id=target_resource,
            start_time=intent.requested_start_time,
            end_time=intent.requested_end_time,
            booker_name=intent.booker_name,
            booker_email=intent.booker_email,
            title=f"Escalated Booking: {intent.booker_name}",
            notes=f"Escalated via triage pipeline. Triage Notes: {intent.triage_notes or 'N/A'}",
        )

        intent.status = IntentStatus.COMPLETED
        intent.escalation_token = None  # Consume single-use token
        await session.flush()
        return appointment
