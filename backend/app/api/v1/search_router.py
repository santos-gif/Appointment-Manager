import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_optional_current_user
from app.database import get_db
from app.models.node import NodeType
from app.models.user import User
from app.schemas.search import SearchResultItem
from app.services.discovery_service import DiscoveryService

router = APIRouter(prefix="/search", tags=["Semantic Resource Discovery"])


@router.get("/discovery", response_model=List[SearchResultItem])
async def search_directory(
    query: Optional[str] = Query(None, description="Natural text query e.g. 'PhD Advisor' or 'Strategy'"),
    node_type: Optional[NodeType] = Query(None, description="Filter by node type"),
    tenant_id: Optional[uuid.UUID] = Query(None, description="Scope search to specific tenant organization"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_optional_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Semantic Resource Discovery Engine:
    Centralized search API that returns allowed nodes based on the booker's authorized viewing permissions.
    """
    results = await DiscoveryService.search_resources(
        session=session,
        query=query,
        node_type=node_type,
        tenant_id=tenant_id,
        user=current_user,
        limit=limit,
        offset=offset,
    )
    return results
