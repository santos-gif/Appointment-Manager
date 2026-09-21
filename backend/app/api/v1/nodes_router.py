import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_optional_current_user
from app.database import get_db
from app.models.node import Node, NodeType, VisibilityTier
from app.models.user import User
from app.schemas.node import NodeCreate, NodeResponse, NodeTreeResponse, NodeUpdate
from app.services.tree_service import TreeService, slugify
from app.services.visibility_evaluator import VisibilityEvaluator

router = APIRouter(prefix="/nodes", tags=["Hierarchical Tree & Multi-Tenancy"])


@router.get("/roots", response_model=List[NodeResponse])
async def list_root_organizations(
    session: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_current_user),
):
    """Lists all Root Organization nodes representing distinct tenant boundaries."""
    stmt = select(Node).where(Node.node_type == NodeType.ORGANIZATION).order_by(Node.name)
    res = await session.execute(stmt)
    roots = res.scalars().all()

    # Filter by visibility
    visible_roots = []
    for r in roots:
        if await VisibilityEvaluator.evaluate_node_visibility(session, r, user):
            visible_roots.append(r)
    return visible_roots


@router.get("/tree/{root_id}", response_model=NodeTreeResponse)
async def get_hierarchical_tree(
    root_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Returns the full polymorphic tree hierarchy rooted at root_id.
    Strictly prunes RESTRICTED or HIDDEN branches that the user lacks privileges to view.
    """
    root = await session.get(Node, root_id)
    if not root:
        raise HTTPException(status_code=404, detail="Root node not found.")

    if not await VisibilityEvaluator.evaluate_node_visibility(session, root, user):
        raise HTTPException(status_code=403, detail="Access to this tenant hierarchy is forbidden.")

    # Fetch all nodes in this tenant
    stmt = select(Node).where(Node.tenant_id == root.tenant_id).order_by(Node.path)
    res = await session.execute(stmt)
    all_nodes = res.scalars().all()

    # Filter nodes by visibility
    allowed_nodes: dict[uuid.UUID, Node] = {}
    for n in all_nodes:
        if await VisibilityEvaluator.evaluate_node_visibility(session, n, user):
            allowed_nodes[n.id] = n

    # Recursively build tree
    def build_tree_node(n: Node) -> NodeTreeResponse:
        resp = NodeTreeResponse.model_validate(n)
        child_objs = [
            build_tree_node(allowed_nodes[child_id])
            for child_id, candidate in allowed_nodes.items()
            if candidate.parent_id == n.id
        ]
        resp.children = child_objs
        return resp

    return build_tree_node(root)


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_current_user),
):
    node = await session.get(Node, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found.")

    if not await VisibilityEvaluator.evaluate_node_visibility(session, node, user):
        raise HTTPException(status_code=403, detail="Forbidden by hierarchical visibility guardrails.")

    return node


@router.post("/", response_model=NodeResponse)
async def create_node(
    payload: NodeCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Creates a new node in the hierarchy under an authorized parent."""
    parent = None
    if payload.parent_id:
        parent = await session.get(Node, payload.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Parent node not found.")
        tenant_id = parent.tenant_id
    else:
        if payload.node_type != NodeType.ORGANIZATION:
            raise HTTPException(status_code=400, detail="Only Organization nodes can be root (parent_id=None).")
        tenant_id = uuid.uuid4()

    slug = payload.slug or slugify(payload.name)
    path = await TreeService.compute_path(session, payload.parent_id, slug)
    node_id = uuid.uuid4()
    if payload.node_type == NodeType.ORGANIZATION and not payload.parent_id:
        tenant_id = node_id

    new_node = Node(
        id=node_id,
        tenant_id=tenant_id,
        node_type=payload.node_type,
        parent_id=payload.parent_id,
        name=payload.name,
        slug=slug,
        path=path,
        description=payload.description,
        metadata_json=payload.metadata_json,
        visibility_settings=payload.visibility_settings.model_dump(),
    )
    session.add(new_node)
    await session.commit()
    await session.refresh(new_node)
    return new_node
