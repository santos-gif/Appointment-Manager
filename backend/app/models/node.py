import enum
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base_types import JsonType, UuidType


class NodeType(str, enum.Enum):
    ORGANIZATION = "organization"  # ROOT: Tenant boundary (e.g. Stanford University, Acme Corp)
    FOLDER = "folder"              # BRANCH 1: Logical grouping (e.g. School of Engineering, HR)
    PROJECT = "project"            # BRANCH 2: Specific context / program (e.g. PhD Advising, Intake)
    RESOURCE = "resource"          # LEAF: Individual human host or physical asset (e.g. Professor, Lab #1)


class VisibilityTier(str, enum.Enum):
    PUBLIC = "PUBLIC"              # Globally searchable and bookable via external directory
    RESTRICTED = "RESTRICTED"      # Stripped from queries unless viewer has matching Organizational Role
    HIDDEN = "HIDDEN"              # Completely invisible except to Super Admins / triage officers


class Node(Base):
    """
    Polymorphic Tree Node implementing the multi-tenant hierarchical governance architecture.
    """
    __tablename__ = "nodes"

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
    node_type: Mapped[NodeType] = mapped_column(
        Enum(NodeType, name="node_type_enum"),
        index=True,
        nullable=False,
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UuidType(),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    # Materialized path for high-performance deep tree traversals (e.g. 'root.eng.phd.advisor')
    path: Mapped[str] = mapped_column(
        String(1024),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Dynamic tagging, capacity bounds, hardware/human attributes, timezone
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(
        JsonType(),
        default=dict,
        nullable=False,
    )

    # Access control matrices & Intent routing configuration:
    # {
    #   "tier": "PUBLIC" | "RESTRICTED" | "HIDDEN",
    #   "allowed_roles": ["student", "faculty"],
    #   "inherit": true,
    #   "triage_project_id": "<uuid-or-none>"
    # }
    visibility_settings: Mapped[Dict[str, Any]] = mapped_column(
        JsonType(),
        default=lambda: {
            "tier": "PUBLIC",
            "allowed_roles": [],
            "inherit": True,
            "triage_project_id": None,
        },
        nullable=False,
    )

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

    # Hierarchical Self-referencing Relationships
    parent: Mapped[Optional["Node"]] = relationship(
        "Node",
        remote_side="Node.id",
        back_populates="children",
        lazy="selectin",
    )
    children: Mapped[List["Node"]] = relationship(
        "Node",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Decoupled Identity Capacity mappings (Only for node_type == 'resource')
    user_mappings: Mapped[List["NodeUserMapping"]] = relationship(
        "NodeUserMapping",
        back_populates="node",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Scheduling Availability Matrix Rules
    availability_rules: Mapped[List["NodeAvailability"]] = relationship(
        "NodeAvailability",
        back_populates="node",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Appointments booked against this node
    appointments: Mapped[List["Appointment"]] = relationship(
        "Appointment",
        back_populates="resource_node",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Booking Intents routed through or targeting this node
    incoming_intents: Mapped[List["BookingIntent"]] = relationship(
        "BookingIntent",
        foreign_keys="BookingIntent.target_node_id",
        back_populates="target_node",
        lazy="selectin",
    )


# Indexes for deep path prefix queries and tenant boundary filtering
Index("ix_nodes_tenant_type", Node.tenant_id, Node.node_type)
Index("ix_nodes_path_pattern", Node.path)
