import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.node import Node, NodeType
from app.models.resource_mapping import NodeUserMapping
from app.models.user import User


@pytest.mark.asyncio
async def test_jit_provisioning_flow(async_client: AsyncClient, db_session: AsyncSession):
    """
    Validates the 4-step JIT Tenant Provisioning lifecycle:
    1. Parse claims (email, organization_domain, department, roles, programs)
    2. Provision root Organization node if not present
    3. Descend tree to provision Folder and Project nodes
    4. Attach User as Leaf Resource node with NodeUserMapping
    5. Set 15m access token & 7d refresh token HttpOnly cookies.
    """
    claims_payload = {
        "sub": "oidc-sub-dr-grace-hopper",
        "email": "grace.hopper@yale.edu",
        "full_name": "Dr. Grace Hopper",
        "organization_domain": "yale.edu",
        "department": "Computer Science Faculty",
        "roles": ["faculty", "compiler_chair"],
        "enrolled_programs": ["Compiler Architecture Lab"],
        "capacity_title": "Chair Professor",
    }

    response = await async_client.post("/api/v1/auth/sso/callback", json=claims_payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert "user" in data
    assert data["user"]["email"] == "grace.hopper@yale.edu"

    # Verify HttpOnly cookies set in response
    cookies = response.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies

    # Verify Root Organization Node created
    stmt_root = select(Node).where(Node.node_type == NodeType.ORGANIZATION, Node.slug == "yale")
    res_root = await db_session.execute(stmt_root)
    root_node = res_root.scalar_one_or_none()
    assert root_node is not None
    assert root_node.metadata_json["domain"] == "yale.edu"

    # Verify Folder Node created
    stmt_folder = select(Node).where(
        Node.node_type == NodeType.FOLDER,
        Node.parent_id == root_node.id,
    )
    res_folder = await db_session.execute(stmt_folder)
    folder_node = res_folder.scalar_one_or_none()
    assert folder_node is not None
    assert folder_node.name == "Computer Science Faculty"

    # Verify Project Node created
    stmt_proj = select(Node).where(
        Node.node_type == NodeType.PROJECT,
        Node.parent_id == folder_node.id,
    )
    res_proj = await db_session.execute(stmt_proj)
    proj_node = res_proj.scalar_one_or_none()
    assert proj_node is not None
    assert proj_node.name == "Compiler Architecture Lab"

    # Verify Leaf Resource Node created
    stmt_res = select(Node).where(
        Node.node_type == NodeType.RESOURCE,
        Node.parent_id == proj_node.id,
    )
    res_leaf = await db_session.execute(stmt_res)
    leaf_node = res_leaf.scalar_one_or_none()
    assert leaf_node is not None
    assert leaf_node.name == "Dr. Grace Hopper"

    # Verify Identity vs Capacity separation: NodeUserMapping exists
    stmt_user = select(User).where(User.email == "grace.hopper@yale.edu")
    res_user = await db_session.execute(stmt_user)
    user = res_user.scalar_one_or_none()
    assert user is not None

    stmt_map = select(NodeUserMapping).where(
        NodeUserMapping.user_id == user.id,
        NodeUserMapping.node_id == leaf_node.id,
    )
    res_map = await db_session.execute(stmt_map)
    mapping = res_map.scalar_one_or_none()
    assert mapping is not None
    assert mapping.capacity_title == "Chair Professor"
