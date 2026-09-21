import contextlib
import uuid
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.api_router import api_router
from app.config import settings
from app.core.exceptions import DomainException
from app.database import Base, engine, async_session_factory
from app.models.node import Node, NodeType, VisibilityTier
from app.models.user import User
from app.models.resource_mapping import NodeUserMapping
from app.models.availability import NodeAvailability
from app.core.security import hash_password


async def seed_initial_demo_data():
    """Seeds initial multi-tenant organizational hierarchies if the database is fresh."""
    async with async_session_factory() as session:
        # Check if root nodes exist
        from sqlalchemy import select
        stmt = select(Node).where(Node.node_type == NodeType.ORGANIZATION)
        res = await session.execute(stmt)
        if res.first():
            return  # Already seeded

        # 1. Root: Stanford University
        stanford_id = uuid.uuid4()
        stanford_org = Node(
            id=stanford_id,
            tenant_id=stanford_id,
            node_type=NodeType.ORGANIZATION,
            name="Stanford University",
            slug="stanford",
            path="stanford",
            description="Leading Global Research Institution & Academic Campus",
            metadata_json={"domain": "stanford.edu", "city": "Stanford, CA"},
            visibility_settings={"tier": VisibilityTier.PUBLIC, "inherit": False},
        )
        session.add(stanford_org)

        # 1b. Folder: School of Engineering
        eng_id = uuid.uuid4()
        eng_folder = Node(
            id=eng_id,
            tenant_id=stanford_id,
            node_type=NodeType.FOLDER,
            parent_id=stanford_id,
            name="School of Engineering",
            slug="engineering",
            path="stanford.engineering",
            description="Computer Science, Mechanical, and Robotics Departments",
            metadata_json={"faculty": "Engineering"},
            visibility_settings={"tier": VisibilityTier.PUBLIC, "inherit": True},
        )
        session.add(eng_folder)

        # 1c. Project: PhD Advising
        phd_id = uuid.uuid4()
        phd_proj = Node(
            id=phd_id,
            tenant_id=stanford_id,
            node_type=NodeType.PROJECT,
            parent_id=eng_id,
            name="PhD Advising & Doctoral Consultations",
            slug="phd-advising",
            path="stanford.engineering.phd-advising",
            description="Academic mentoring and research defense sessions",
            metadata_json={"office_hours": "Mon-Wed"},
            visibility_settings={"tier": VisibilityTier.PUBLIC, "inherit": True},
        )
        session.add(phd_proj)

        # 1d. Resource Leaf: Dr. Eleanor Smith
        dr_smith_user_id = uuid.uuid4()
        smith_user = User(
            id=dr_smith_user_id,
            email="dr.smith@stanford.edu",
            full_name="Dr. Eleanor Smith",
            hashed_password=hash_password("academic2026"),
            roles=["faculty", "phd_advisor"],
            is_active=True,
            is_superuser=False,
        )
        session.add(smith_user)

        smith_res_id = uuid.uuid4()
        smith_res_node = Node(
            id=smith_res_id,
            tenant_id=stanford_id,
            node_type=NodeType.RESOURCE,
            parent_id=phd_id,
            name="Dr. Eleanor Smith (Robotics & AI)",
            slug="dr-eleanor-smith",
            path="stanford.engineering.phd-advising.dr-eleanor-smith",
            description="Full Professor of Computer Science & Robotics Chair",
            metadata_json={"capacity_title": "Professor & Primary Advisor", "timezone": "America/Los_Angeles"},
            visibility_settings={"tier": VisibilityTier.PUBLIC, "allowed_roles": ["student", "faculty"], "inherit": True},
        )
        session.add(smith_res_node)

        session.add(
            NodeUserMapping(
                id=uuid.uuid4(),
                user_id=dr_smith_user_id,
                node_id=smith_res_id,
                capacity_title="PhD Primary Advisor",
                allocation_percentage=100.0,
                is_primary=True,
            )
        )

        # Availability for Dr. Smith: Monday & Wednesday 09:00 - 13:00
        session.add(
            NodeAvailability(
                id=uuid.uuid4(),
                node_id=smith_res_id,
                day_of_week=0,  # Monday
                start_time="09:00",
                end_time="13:00",
                slot_duration_minutes=30,
                buffer_minutes=10,
            )
        )
        session.add(
            NodeAvailability(
                id=uuid.uuid4(),
                node_id=smith_res_id,
                day_of_week=2,  # Wednesday
                start_time="10:00",
                end_time="14:00",
                slot_duration_minutes=30,
                buffer_minutes=10,
            )
        )

        # 2. Root: Acme Global Enterprise Corporation
        acme_id = uuid.uuid4()
        acme_org = Node(
            id=acme_id,
            tenant_id=acme_id,
            node_type=NodeType.ORGANIZATION,
            name="Acme Global Corporation",
            slug="acme",
            path="acme",
            description="Fortune 50 Enterprise Conglomerate",
            metadata_json={"domain": "acmecorp.com"},
            visibility_settings={"tier": VisibilityTier.PUBLIC, "inherit": False},
        )
        session.add(acme_org)

        # 2b. Folder: Executive Leadership
        exec_folder_id = uuid.uuid4()
        exec_folder = Node(
            id=exec_folder_id,
            tenant_id=acme_id,
            node_type=NodeType.FOLDER,
            parent_id=acme_id,
            name="Executive Leadership Suite",
            slug="exec-suite",
            path="acme.exec-suite",
            description="C-Suite & Board of Directors",
            metadata_json={"access_level": "RESTRICTED"},
            visibility_settings={"tier": VisibilityTier.RESTRICTED, "allowed_roles": ["executive", "admin"], "inherit": True},
        )
        session.add(exec_folder)

        # 2c. Project: Strategic Partnerships Intake (Triage Node)
        triage_proj_id = uuid.uuid4()
        triage_proj = Node(
            id=triage_proj_id,
            tenant_id=acme_id,
            node_type=NodeType.PROJECT,
            parent_id=exec_folder_id,
            name="Partnership & Strategic Intake Portal",
            slug="strategic-intake",
            path="acme.exec-suite.strategic-intake",
            description="Screening pipeline for external corporate partnership requests",
            metadata_json={"pipeline": "intent_triage"},
            visibility_settings={"tier": VisibilityTier.PUBLIC, "inherit": False},
        )
        session.add(triage_proj)

        # 2d. Hidden Executive Leaf: Alex Vance (EVP Strategy)
        vance_user_id = uuid.uuid4()
        vance_user = User(
            id=vance_user_id,
            email="alex.vance@acmecorp.com",
            full_name="Alex Vance (EVP Strategy)",
            hashed_password=hash_password("executive2026"),
            roles=["executive", "c-level", "admin"],
            is_active=True,
            is_superuser=True,
        )
        session.add(vance_user)

        vance_res_id = uuid.uuid4()
        vance_res_node = Node(
            id=vance_res_id,
            tenant_id=acme_id,
            node_type=NodeType.RESOURCE,
            parent_id=triage_proj_id,
            name="Alex Vance (EVP of Strategy)",
            slug="alex-vance",
            path="acme.exec-suite.strategic-intake.alex-vance",
            description="Executive Vice President - Calendar protected by Intent-Based Routing Guardrail",
            metadata_json={"capacity_title": "EVP Corporate Strategy", "timezone": "America/New_York"},
            # Notice HIDDEN tier with triage_project_id pointing to Partnership Intake!
            visibility_settings={
                "tier": VisibilityTier.HIDDEN,
                "allowed_roles": ["executive", "admin"],
                "inherit": True,
                "triage_project_id": str(triage_proj_id),
            },
        )
        session.add(vance_res_node)

        session.add(
            NodeUserMapping(
                id=uuid.uuid4(),
                user_id=vance_user_id,
                node_id=vance_res_id,
                capacity_title="Executive Vice President",
                allocation_percentage=100.0,
                is_primary=True,
            )
        )

        await session.commit()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Ensure database schema is initialized
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed demonstration hierarchies
    try:
        await seed_initial_demo_data()
    except Exception as e:
        print(f"Warning: demo data seeding skipped or encountered error: {e}")

    yield

    await engine.dispose()


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="Hierarchical, Multi-Tenant Resource Governance and Scheduling Engine with Asyncpg and SQLAlchemy 2.0",
        lifespan=lifespan,
    )

    # CORS configuration allowing credentials (HttpOnly cookies)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Domain Exception Handler
    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": exc.code, "message": exc.message, "details": exc.details},
        )

    # Register API v1 routes
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/health", tags=["System Health"])
    async def health_check():
        return {
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "engine": "FastAPI + SQLAlchemy 2.0 Async + Asyncpg",
        }

    return app


app = create_application()
