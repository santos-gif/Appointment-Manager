import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.node import NodeType, VisibilityTier


class SemanticSearchQuery(BaseModel):
    query: Optional[str] = None
    tags: List[str] = []
    node_type: Optional[NodeType] = None
    tenant_id: Optional[uuid.UUID] = None
    limit: int = 50
    offset: int = 0


class SearchResultItem(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    node_type: NodeType
    name: str
    slug: str
    path: str
    description: Optional[str]
    metadata_json: Dict[str, Any]
    visibility_tier: VisibilityTier
    capacity_title: Optional[str] = None
    direct_booking_allowed: bool = True
    triage_required: bool = False
