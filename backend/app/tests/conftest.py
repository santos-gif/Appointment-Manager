import asyncio
import uuid
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.api.deps import get_db
from app.config import settings
from app.core.security import create_access_token, hash_password
from app.database import Base
from app.main import app
from app.models.node import Node, NodeType, VisibilityTier
from app.models.user import User

# In-memory async SQLite engine for isolated rapid unit/integration tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
TestSessionFactory = async_sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionFactory() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        async with TestSessionFactory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def seed_data(db_session: AsyncSession):
    """Seed test tenant with Public, Restricted, and Hidden nodes."""
    tenant_id = uuid.uuid4()
    org_node = Node(
        id=tenant_id,
        tenant_id=tenant_id,
        node_type=NodeType.ORGANIZATION,
        name="Test University",
        slug="test-uni",
        path="test-uni",
        metadata_json={"domain": "test.edu"},
        visibility_settings={"tier": VisibilityTier.PUBLIC, "inherit": False},
    )
    db_session.add(org_node)

    folder_node = Node(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        node_type=NodeType.FOLDER,
        parent_id=tenant_id,
        name="Engineering Dept",
        slug="engineering",
        path="test-uni.engineering",
        metadata_json={},
        visibility_settings={"tier": VisibilityTier.PUBLIC, "inherit": True},
    )
    db_session.add(folder_node)

    # Restricted node for internal members only
    restricted_proj = Node(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        node_type=NodeType.PROJECT,
        parent_id=folder_node.id,
        name="Internal Faculty Grants",
        slug="internal-grants",
        path="test-uni.engineering.internal-grants",
        metadata_json={},
        visibility_settings={"tier": VisibilityTier.RESTRICTED, "allowed_roles": ["faculty"], "inherit": True},
    )
    db_session.add(restricted_proj)

    # Triage intake portal project
    triage_portal = Node(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        node_type=NodeType.PROJECT,
        parent_id=folder_node.id,
        name="Dean Consultation Intake",
        slug="dean-intake",
        path="test-uni.engineering.dean-intake",
        metadata_json={},
        visibility_settings={"tier": VisibilityTier.PUBLIC, "inherit": False},
    )
    db_session.add(triage_portal)

    # Hidden Dean Executive Resource Node
    hidden_dean = Node(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        node_type=NodeType.RESOURCE,
        parent_id=folder_node.id,
        name="Dean of Engineering",
        slug="dean",
        path="test-uni.engineering.dean",
        metadata_json={},
        visibility_settings={
            "tier": VisibilityTier.HIDDEN,
            "allowed_roles": ["admin", "executive"],
            "inherit": True,
            "triage_project_id": str(triage_portal.id),
        },
    )
    db_session.add(hidden_dean)

    # Public Professor Resource Node
    public_prof = Node(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        node_type=NodeType.RESOURCE,
        parent_id=folder_node.id,
        name="Prof. Alan Turing",
        slug="prof-turing",
        path="test-uni.engineering.prof-turing",
        metadata_json={},
        visibility_settings={"tier": VisibilityTier.PUBLIC, "inherit": True},
    )
    db_session.add(public_prof)

    # Regular Student User
    student_user = User(
        id=uuid.uuid4(),
        email="student@test.edu",
        full_name="Alice Student",
        hashed_password=hash_password("pass123"),
        roles=["student"],
        is_active=True,
    )
    db_session.add(student_user)

    # Faculty User
    faculty_user = User(
        id=uuid.uuid4(),
        email="faculty@test.edu",
        full_name="Bob Faculty",
        hashed_password=hash_password("pass123"),
        roles=["faculty"],
        is_active=True,
    )
    db_session.add(faculty_user)

    # Admin User
    admin_user = User(
        id=uuid.uuid4(),
        email="admin@test.edu",
        full_name="Charlie Admin",
        hashed_password=hash_password("pass123"),
        roles=["admin"],
        is_active=True,
        is_superuser=True,
    )
    db_session.add(admin_user)

    await db_session.commit()

    return {
        "org_node": org_node,
        "folder_node": folder_node,
        "restricted_proj": restricted_proj,
        "triage_portal": triage_portal,
        "hidden_dean": hidden_dean,
        "public_prof": public_prof,
        "student_user": student_user,
        "faculty_user": faculty_user,
        "admin_user": admin_user,
    }
