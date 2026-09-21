import uuid
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base_types import UuidType


class NodeAvailability(Base):
    """
    Availability matrix configuration for a specific node context.
    Allows hosts to declare distinct availability per mapped node
    (e.g., Free for 'PhD Advising' Mondays 09:00-13:00; Free for 'Lab Equipment' Wednesdays 14:00-18:00).
    """
    __tablename__ = "node_availabilities"

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType(),
        primary_key=True,
        default=uuid.uuid4,
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UuidType(),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # 0 = Monday, 1 = Tuesday, ..., 6 = Sunday (Nullable if specific_date override is used)
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Specific date override (for one-off dates / holidays / special office hours)
    specific_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # HH:MM 24h format (e.g. "09:00", "17:00")
    start_time: Mapped[str] = mapped_column(String(5), nullable=False, default="09:00")
    end_time: Mapped[str] = mapped_column(String(5), nullable=False, default="17:00")

    slot_duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    buffer_minutes: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    node: Mapped["Node"] = relationship("Node", back_populates="availability_rules")


Index("ix_avail_node_day", NodeAvailability.node_id, NodeAvailability.day_of_week)
Index("ix_avail_node_date", NodeAvailability.node_id, NodeAvailability.specific_date)
