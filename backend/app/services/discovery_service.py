import uuid
from typing import List, Optional
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.node import Node, NodeType, VisibilityTier
from app.models.user import User
from app.schemas.search import SearchResultItem
from app.services.visibility_evaluator import VisibilityEvaluator


class DiscoveryService:
    @staticmethod
    async def search_resources(
        session: AsyncSession,
        query: Optional[str] = None,
        node_type: Optional[NodeType] = None,
        tenant_id: Optional[uuid.UUID] = None,
        user: Optional[User] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SearchResultItem]:
        """
        Queries the tree and filters matching nodes based on the booker's authorized viewing permissions.
        """
        stmt = select(Node)
        if node_type:
            stmt = stmt.where(Node.node_type == node_type)
        if tenant_id:
            stmt = stmt.where(Node.tenant_id == tenant_id)

        if query:
            q_lower = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    Node.name.ilike(q_lower),
                    Node.description.ilike(q_lower),
                    Node.path.ilike(q_lower),
                )
            )

        stmt = stmt.limit(limit * 2).offset(offset)  # Over-fetch for visibility filtering
        res = await session.execute(stmt)
        candidates = res.scalars().all()

        results: List[SearchResultItem] = []
        for node in candidates:
            # Enforce hierarchical RBAC & visibility policy
            is_visible = await VisibilityEvaluator.evaluate_node_visibility(
                session=session,
                node=node,
                user=user,
            )
            if not is_visible:
                continue

            v_settings = node.visibility_settings or {}
            tier_str = v_settings.get("tier", VisibilityTier.PUBLIC)
            try:
                tier = VisibilityTier(tier_str)
            except ValueError:
                tier = VisibilityTier.PUBLIC

            requires_triage = VisibilityEvaluator.requires_intent_triage(node)

            results.append(
                SearchResultItem(
                    id=node.id,
                    tenant_id=node.tenant_id,
                    node_type=node.node_type,
                    name=node.name,
                    slug=node.slug,
                    path=node.path,
                    description=node.description,
                    metadata_json=node.metadata_json,
                    visibility_tier=tier,
                    capacity_title=node.metadata_json.get("capacity_title"),
                    direct_booking_allowed=not requires_triage,
                    triage_required=requires_triage,
                )
            )
            if len(results) >= limit:
                break

        return results
