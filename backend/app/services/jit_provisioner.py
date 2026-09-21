import uuid
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password
from app.models.node import Node, NodeType, VisibilityTier
from app.models.resource_mapping import NodeUserMapping
from app.models.user import User
from app.schemas.auth import OIDCClaims
from app.services.tree_service import TreeService, slugify


class JITProvisioner:
    """
    Just-In-Time (JIT) Multi-Tenant Hierarchy Auto-Provisioning Engine.
    Executes an atomic async provisioning lifecycle on successful SSO claims inspection.
    """

    @staticmethod
    async def provision_user_and_hierarchy(
        session: AsyncSession,
        claims: OIDCClaims,
    ) -> Tuple[User, Node]:
        """
        Executes the 4-step JIT Tenant Provisioning lifecycle:
        1. Parse claims & sync System Identity User.
        2. Root Provisioning: Check/create Organization root for organization_domain.
        3. Hierarchy Descent: Check/create Folder (department) and Project (enrolled_programs).
        4. Leaf Attachment: Instantiate/link User as a Resource node under computed leaf path.
        """
        # Step 1: Sync or create global User System Identity
        stmt = select(User).where(User.email == claims.email)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            user = User(
                id=uuid.uuid4(),
                email=claims.email,
                full_name=claims.full_name,
                hashed_password=hash_password(uuid.uuid4().hex),  # SSO managed
                roles=claims.roles,
                is_active=True,
                is_superuser=("admin" in claims.roles or "superadmin" in claims.roles),
            )
            session.add(user)
            await session.flush()
        else:
            # Refresh roles
            user.full_name = claims.full_name
            user.roles = list(set(user.roles + claims.roles))
            await session.flush()

        # Step 2: Root Tenant Node (Organization)
        root_slug = slugify(claims.organization_domain.split(".")[0])
        root_node = await TreeService.get_root_by_domain(session, claims.organization_domain)
        if not root_node:
            root_id = uuid.uuid4()
            org_name = claims.organization_domain.split(".")[0].capitalize() + " Organization"
            root_node = Node(
                id=root_id,
                tenant_id=root_id,  # Self-referencing tenant root boundary
                node_type=NodeType.ORGANIZATION,
                parent_id=None,
                name=org_name,
                slug=root_slug,
                path=root_slug,
                description=f"Auto-provisioned root tenant for {claims.organization_domain}",
                metadata_json={"domain": claims.organization_domain, "provisioned_via": "JIT_SSO"},
                visibility_settings={"tier": VisibilityTier.PUBLIC, "inherit": False},
            )
            session.add(root_node)
            await session.flush()

        tenant_id = root_node.id

        # Step 3: Hierarchy Descent
        # 3a. Branch 1: Folder (Department / Faculty)
        dept_name = claims.department or "General Faculty"
        folder_slug = slugify(dept_name)
        folder_node = await TreeService.get_direct_child_by_slug(
            session, root_node.id, folder_slug, NodeType.FOLDER
        )
        if not folder_node:
            folder_id = uuid.uuid4()
            folder_path = f"{root_node.path}.{folder_slug}"
            folder_node = Node(
                id=folder_id,
                tenant_id=tenant_id,
                node_type=NodeType.FOLDER,
                parent_id=root_node.id,
                name=dept_name,
                slug=folder_slug,
                path=folder_path,
                description=f"Department folder for {dept_name}",
                metadata_json={"department": dept_name},
                visibility_settings={"tier": VisibilityTier.PUBLIC, "inherit": True},
            )
            session.add(folder_node)
            await session.flush()

        # 3b. Branch 2: Project (Enrolled Program / Working Initiative)
        program_name = claims.enrolled_programs[0] if claims.enrolled_programs else "General Consultations"
        project_slug = slugify(program_name)
        project_node = await TreeService.get_direct_child_by_slug(
            session, folder_node.id, project_slug, NodeType.PROJECT
        )
        if not project_node:
            project_id = uuid.uuid4()
            project_path = f"{folder_node.path}.{project_slug}"
            project_node = Node(
                id=project_id,
                tenant_id=tenant_id,
                node_type=NodeType.PROJECT,
                parent_id=folder_node.id,
                name=program_name,
                slug=project_slug,
                path=project_path,
                description=f"Program initiative for {program_name}",
                metadata_json={"program": program_name},
                visibility_settings={"tier": VisibilityTier.PUBLIC, "inherit": True},
            )
            session.add(project_node)
            await session.flush()

        # Step 4: Leaf Attachment (Resource Node & Capacity Mapping)
        user_leaf_slug = slugify(claims.full_name or claims.email.split("@")[0])
        resource_node = await TreeService.get_direct_child_by_slug(
            session, project_node.id, user_leaf_slug, NodeType.RESOURCE
        )
        if not resource_node:
            resource_id = uuid.uuid4()
            resource_path = f"{project_node.path}.{user_leaf_slug}"
            
            # Decide visibility tier based on roles (Executive gets HIDDEN, faculty gets PUBLIC or RESTRICTED)
            is_exec = "executive" in claims.roles or "c-level" in claims.roles
            tier = VisibilityTier.HIDDEN if is_exec else VisibilityTier.PUBLIC

            resource_node = Node(
                id=resource_id,
                tenant_id=tenant_id,
                node_type=NodeType.RESOURCE,
                parent_id=project_node.id,
                name=claims.full_name,
                slug=user_leaf_slug,
                path=resource_path,
                description=f"Operational capacity node for {claims.full_name}",
                metadata_json={
                    "email": claims.email,
                    "timezone": "UTC",
                    "roles": claims.roles,
                    "capacity_bounds": {"max_sessions_per_day": 6},
                },
                visibility_settings={
                    "tier": tier,
                    "allowed_roles": claims.roles,
                    "inherit": True,
                    "triage_project_id": str(project_node.id) if is_exec else None,
                },
            )
            session.add(resource_node)
            await session.flush()

        # Step 4b: Ensure NodeUserMapping bridges User to Resource Node
        stmt_map = select(NodeUserMapping).where(
            NodeUserMapping.user_id == user.id,
            NodeUserMapping.node_id == resource_node.id,
        )
        res_map = await session.execute(stmt_map)
        mapping = res_map.scalar_one_or_none()
        if not mapping:
            capacity_title = claims.capacity_title or (
                "Executive Director" if "executive" in claims.roles else "Academic Advisor"
            )
            mapping = NodeUserMapping(
                id=uuid.uuid4(),
                user_id=user.id,
                node_id=resource_node.id,
                capacity_title=capacity_title,
                allocation_percentage=100.0,
                is_primary=True,
            )
            session.add(mapping)
            await session.flush()

        return user, resource_node
