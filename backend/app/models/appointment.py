import enum
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base_types import UuidType


class AppointmentStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class Appointment(Base):
    """
    Reserved appointment slot. Concurrency is strictly enforced using PostgreSQL
    row-level transaction locks ('SELECT FOR UPDATE') within the async session.
    """
    __tablename__ = "appointments"

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
    resource_node_id: Mapped[uuid.UUID] = mapped_column(
        UuidType(),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    booker_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UuidType(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    booker_name: Mapped[str] = mapped_column(String(255), nullable=False)
    booker_email: Mapped[str] = mapped_column(String(255), nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Scheduled Session")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status_enum"),
        default=AppointmentStatus.CONFIRMED,
        nullable=False,
        index=True,
    )

    # Escrow & Payment details
    payment_status: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    payment_amount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

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
    resource_node: Mapped["Node"] = relationship("Node", back_populates="appointments")


# High performance composite index for conflict-free calendar queries and row locks
Index(
    "ix_appointments_conflict_lookup",
    Appointment.resource_node_id,
    Appointment.status,
    Appointment.start_time,
    Appointment.end_time,
)
