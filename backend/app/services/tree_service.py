import re
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.node import Node, NodeType


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-") or "node"


class TreeService:
    @staticmethod
    async def get_node_by_id(session: AsyncSession, node_id: uuid.UUID) -> Optional[Node]:
        stmt = select(Node).where(Node.id == node_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_root_by_slug(session: AsyncSession, slug: str) -> Optional[Node]:
        stmt = select(Node).where(Node.node_type == NodeType.ORGANIZATION, Node.slug == slug)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_root_by_domain(session: AsyncSession, domain: str) -> Optional[Node]:
        """Find root organization by domain stored in metadata_json or name."""
        stmt = select(Node).where(Node.node_type == NodeType.ORGANIZATION)
        result = await session.execute(stmt)
        roots = result.scalars().all()
        for root in roots:
            meta_domain = root.metadata_json.get("domain")
            if meta_domain and meta_domain.lower() == domain.lower():
                return root
            if root.slug == slugify(domain.split(".")[0]):
                return root
        return None

    @staticmethod
    async def get_direct_child_by_slug(
        session: AsyncSession,
        parent_id: uuid.UUID,
        slug: str,
        node_type: NodeType,
    ) -> Optional[Node]:
        stmt = select(Node).where(
            Node.parent_id == parent_id,
            Node.slug == slug,
            Node.node_type == node_type,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def compute_path(session: AsyncSession, parent_id: Optional[uuid.UUID], node_slug: str) -> str:
        if not parent_id:
            return node_slug
        parent = await TreeService.get_node_by_id(session, parent_id)
        if not parent:
            return node_slug
        return f"{parent.path}.{node_slug}"

    @staticmethod
    async def get_subtree(
        session: AsyncSession,
        root_node_id: uuid.UUID,
    ) -> Optional[Node]:
        """Loads a tree starting from root_node_id with eager loaded children."""
        root = await TreeService.get_node_by_id(session, root_node_id)
        if not root:
            return None
        return root

    @staticmethod
    async def get_all_descendants(
        session: AsyncSession,
        parent_path: str,
    ) -> List[Node]:
        """Gets all descendants using path prefix matching."""
        pattern = f"{parent_path}.%"
        stmt = select(Node).where(Node.path.like(pattern)).order_by(Node.path)
        result = await session.execute(stmt)
        return list(result.scalars().all())
