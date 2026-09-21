import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base_types import JsonType, UuidType


class CalendarIntegration(Base):
    """
    Multi-Calendar Synchronization state for external providers (Google Calendar & Microsoft Outlook).
    Used to aggregate real-time external busy slots to prevent host scheduling conflicts.
    """
    __tablename__ = "calendar_integrations"

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType(),
        primary_key=True,
        default=uuid.uuid4,
    )
    resource_node_id: Mapped[uuid.UUID] = mapped_column(
        UuidType(),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # 'google' | 'outlook'
    account_email: Mapped[str] = mapped_column(String(255), nullable=False)
    sync_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    access_token_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_status_message: Mapped[str] = mapped_column(String(255), default="Connected and Healthy")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class PaymentEscrowConfig(Base):
    """
    Escrow and payment terms for paid consultations across nodes.
    Supports Stripe and PayPal checkout flows.
    """
    __tablename__ = "payment_escrow_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType(),
        primary_key=True,
        default=uuid.uuid4,
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UuidType(),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), default="stripe", nullable=False)  # 'stripe' | 'paypal'
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    amount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Policy: 'instant_capture', 'escrow_hold_until_session', 'refundable_until_24h'
    escrow_policy: Mapped[str] = mapped_column(String(100), default="escrow_hold_until_session", nullable=False)
    account_connected_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class IntakeFormSchema(Base):
    """
    Custom metadata intake question schema created via the Provider's Form Builder.
    Captured during booker checkout.
    """
    __tablename__ = "intake_form_schemas"

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType(),
        primary_key=True,
        default=uuid.uuid4,
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UuidType(),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), default="Pre-Consultation Intake Form", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Schema array:
    # [
    #   {"id": "q1", "type": "text", "label": "Research topic or project context", "required": true},
    #   {"id": "q2", "type": "select", "label": "Urgency Level", "options": ["Low", "High", "Critical"], "required": true}
    # ]
    fields_json: Mapped[List[Dict[str, Any]]] = mapped_column(
        JsonType(),
        default=list,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
