import pytest
from httpx import AsyncClient
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_visibility_filtering(async_client: AsyncClient, seed_data: dict):
    """
    Validates hierarchical RBAC and visibility tiers:
    - PUBLIC: visible to everyone
    - RESTRICTED: stripped unless user has allowed role
    - HIDDEN: completely omitted unless superadmin / triage role
    """
    student = seed_data["student_user"]
    faculty = seed_data["faculty_user"]
    admin = seed_data["admin_user"]
    root_id = seed_data["org_node"].id

    # 1. Anonymous viewer: should only see PUBLIC nodes
    resp_anon = await async_client.get("/api/v1/search/discovery")
    assert resp_anon.status_code == 200
    anon_nodes = [item["name"] for item in resp_anon.json()]
    assert "Prof. Alan Turing" in anon_nodes
    assert "Dean of Engineering" not in anon_nodes
    assert "Internal Faculty Grants" not in anon_nodes

    # 2. Student viewer (roles: ['student']): cannot see RESTRICTED or HIDDEN
    student_token = create_access_token(str(student.id), student.email, student.roles)
    resp_student = await async_client.get(
        "/api/v1/search/discovery",
        cookies={"access_token": student_token},
    )
    assert resp_student.status_code == 200
    student_nodes = [item["name"] for item in resp_student.json()]
    assert "Prof. Alan Turing" in student_nodes
    assert "Internal Faculty Grants" not in student_nodes
    assert "Dean of Engineering" not in student_nodes

    # 3. Faculty viewer (roles: ['faculty']): CAN see RESTRICTED, but not HIDDEN
    faculty_token = create_access_token(str(faculty.id), faculty.email, faculty.roles)
    resp_faculty = await async_client.get(
        "/api/v1/search/discovery",
        cookies={"access_token": faculty_token},
    )
    assert resp_faculty.status_code == 200
    faculty_nodes = [item["name"] for item in resp_faculty.json()]
    assert "Prof. Alan Turing" in faculty_nodes
    assert "Internal Faculty Grants" in faculty_nodes
    assert "Dean of Engineering" not in faculty_nodes

    # 4. Super Admin viewer (roles: ['admin'], is_superuser=True): can see ALL nodes
    admin_token = create_access_token(str(admin.id), admin.email, admin.roles)
    resp_admin = await async_client.get(
        "/api/v1/search/discovery",
        cookies={"access_token": admin_token},
    )
    assert resp_admin.status_code == 200
    admin_nodes = [item["name"] for item in resp_admin.json()]
    assert "Prof. Alan Turing" in admin_nodes
    assert "Internal Faculty Grants" in admin_nodes
    assert "Dean of Engineering" in admin_nodes
