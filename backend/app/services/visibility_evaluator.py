from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.node import Node, VisibilityTier
from app.models.user import User


class VisibilityEvaluator:
    """
    Evaluates hierarchical access control matrices across the tree.
    Enforces PUBLIC, RESTRICTED (Internal/Role-gated), and HIDDEN (Admin/Executive-gated) tiers.
    """

    @staticmethod
    async def evaluate_node_visibility(
        session: AsyncSession,
        node: Node,
        user: Optional[User],
        user_roles: Optional[List[str]] = None,
    ) -> bool:
        """
        Determines whether the given user (or anonymous viewer) can view this node.
        Descendants inherit parent visibility unless explicitly overridden.
        """
        # Superusers can always view all nodes
        if user and user.is_superuser:
            return True

        roles = set(user_roles or (user.roles if user else []))

        # Check this node's explicit visibility settings
        settings = node.visibility_settings or {}
        tier_str = settings.get("tier", VisibilityTier.PUBLIC)
        try:
            tier = VisibilityTier(tier_str)
        except ValueError:
            tier = VisibilityTier.PUBLIC

        allowed_roles = set(settings.get("allowed_roles", []))

        # Evaluate current tier
        if tier == VisibilityTier.HIDDEN:
            # Hidden nodes are invisible to public and regular internal users
            if not user:
                return False
            # Allow if user has explicit 'admin' or 'executive_triage' role
            if not bool(roles & {"admin", "superadmin", "executive_triage"}):
                return False

        elif tier == VisibilityTier.RESTRICTED:
            # Restricted nodes require matching organizational roles
            if not user:
                return False
            if allowed_roles and not bool(roles & allowed_roles) and not bool(roles & {"admin", "superadmin"}):
                return False

        # If policy inherits from parent, also check parent node
        if settings.get("inherit", True) and node.parent_id:
            parent = await session.get(Node, node.parent_id)
            if parent:
                parent_visible = await VisibilityEvaluator.evaluate_node_visibility(
                    session, parent, user, list(roles)
                )
                if not parent_visible:
                    return False

        return True

    @staticmethod
    def requires_intent_triage(node: Node) -> bool:
        """
        Returns True if booking requests must be routed through the indirect Intent Pipeline
        rather than directly scheduling on the resource's calendar.
        """
        settings = node.visibility_settings or {}
        tier = settings.get("tier", VisibilityTier.PUBLIC)
        triage_id = settings.get("triage_project_id")
        return (tier == VisibilityTier.HIDDEN) or (triage_id is not None)

    @staticmethod
    def get_triage_project_id(node: Node) -> Optional[str]:
        settings = node.visibility_settings or {}
        return settings.get("triage_project_id")
