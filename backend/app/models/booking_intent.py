import enum
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base_types import JsonType, UuidType


class IntentStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RESCHEDULED = "RESCHEDULED"
    COMPLETED = "COMPLETED"


class BookingIntent(Base):
    """
    Screening and triage pipeline for protected / hidden nodes.
    Instead of directly reserving an executive or high-security asset, public requests
    are captured as a BookingIntent routed to a triage Project Node.
    """
    __tablename__ = "booking_intents"

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType(),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UuidType(),
        index=True,
        nullable=False,
    )
    # The protected resource node that the booker initially desires
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        UuidType(),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # The triage intake project node handling the evaluation
    triage_project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UuidType(),
        ForeignKey("nodes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # The escalated node (if approved and routed upward)
    escalated_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UuidType(),
        ForeignKey("nodes.id", ondelete="SET NULL"),
        nullable=True,
    )

    booker_name: Mapped[str] = mapped_column(String(255), nullable=False)
    booker_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    requested_start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    requested_end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    status: Mapped[IntentStatus] = mapped_column(
        Enum(IntentStatus, name="intent_status_enum"),
        default=IntentStatus.PENDING_REVIEW,
        nullable=False,
        index=True,
    )
    
    intake_responses: Mapped[Dict[str, Any]] = mapped_column(
        JsonType(),
        default=dict,
        nullable=False,
    )
    triage_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    escalation_token: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    target_node: Mapped["Node"] = relationship(
        "Node",
        foreign_keys=[target_node_id],
        back_populates="incoming_intents",
    )
