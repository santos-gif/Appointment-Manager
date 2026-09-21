import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base_types import UuidType


class NodeUserMapping(Base):
    """
    Decouples System Identity (User) from Organizational Capacity (Resource Node).
    A single User can be attached to multiple Resource Nodes across organizations with distinct
    titles, capacities, and permissions.
    """
    __tablename__ = "node_user_mappings"

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UuidType(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UuidType(),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    capacity_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="Assigned Host",
    )  # e.g., "PhD Primary Advisor", "Executive Consultant", "Lab Custodian"
    allocation_percentage: Mapped[float] = mapped_column(
        Float,
        default=100.0,
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="resource_mappings")
    node: Mapped["Node"] = relationship("Node", back_populates="user_mappings")


Index("ix_user_node_unique", NodeUserMapping.user_id, NodeUserMapping.node_id, unique=True)
