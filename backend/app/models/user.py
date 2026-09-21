import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base_types import JsonType, UuidType


class User(Base):
    """
    Global System Identity decoupled from Contextual Organizational Capacity.
    A single User can be mapped as a 'Resource' node across multiple distinct Organizations or Faculties.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType(),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Global roles (e.g. ['admin', 'faculty_staff', 'student'])
    roles: Mapped[List[str]] = mapped_column(JsonType(), default=list, nullable=False)
    
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
    resource_mappings: Mapped[List["NodeUserMapping"]] = relationship(
        "NodeUserMapping",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
