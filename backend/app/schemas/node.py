from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.node import NodeType, VisibilityTier


class VisibilitySettingsSchema(BaseModel):
    tier: VisibilityTier = Field(default=VisibilityTier.PUBLIC, description="Exposure tier")
    allowed_roles: List[str] = Field(default_factory=list, description="Roles permitted to view restricted node")
    inherit: bool = Field(default=True, description="Whether to inherit parent visibility policy")
    triage_project_id: Optional[uuid.UUID] = Field(default=None, description="Intake project node for screening")


class NodeCreate(BaseModel):
    tenant_id: Optional[uuid.UUID] = None
    node_type: NodeType
    parent_id: Optional[uuid.UUID] = None
    name: str = Field(min_length=1, max_length=255)
    slug: Optional[str] = None
    description: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    visibility_settings: VisibilitySettingsSchema = Field(default_factory=VisibilitySettingsSchema)


class NodeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    visibility_settings: Optional[VisibilitySettingsSchema] = None


class NodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    node_type: NodeType
    parent_id: Optional[uuid.UUID]
    path: str
    name: str
    slug: str
    description: Optional[str]
    metadata_json: Dict[str, Any]
    visibility_settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class NodeTreeResponse(NodeResponse):
    children: List[NodeTreeResponse] = Field(default_factory=list)
