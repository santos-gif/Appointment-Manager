import uuid
from typing import Optional
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.security import (
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    set_auth_cookies,
    verify_password,
)
from app.database import get_db
from app.models.node import Node
from app.models.resource_mapping import NodeUserMapping
from app.models.user import User
from app.schemas.auth import LoginRequest, MeResponse, OIDCClaims, ResourceNodeBrief, UserResponse
from app.services.jit_provisioner import JITProvisioner

router = APIRouter(prefix="/auth", tags=["Enterprise Authentication & SSO"])


@router.post("/login")
async def login(
    payload: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
):
    """
    Standard email/password login. Sets HttpOnly cookies for:
    - access_token (15 minutes)
    - refresh_token (7 days)
    """
    stmt = select(User).where(User.email == payload.email)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    access_token = create_access_token(str(user.id), user.email, user.roles)
    refresh_token = create_refresh_token(str(user.id))

    set_auth_cookies(response, access_token, refresh_token)

    return {
        "status": "success",
        "message": "Authentication successful. HttpOnly session cookies issued.",
        "user": UserResponse.model_validate(user),
    }


@router.post("/refresh")
async def refresh_tokens(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    session: AsyncSession = Depends(get_db),
):
    """
    Refreshes session using the 7-day HttpOnly refresh_token cookie.
    Rotates both access and refresh cookies.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token cookie.",
        )

    try:
        payload = decode_jwt_token(refresh_token)
        if payload.get("token_type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type.")
        user_id = uuid.UUID(payload.get("sub"))
        user = await session.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User account is inactive or not found.")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired or malformed refresh token.")

    # Issue rotated token pair
    new_access_token = create_access_token(str(user.id), user.email, user.roles)
    new_refresh_token = create_refresh_token(str(user.id))

    set_auth_cookies(response, new_access_token, new_refresh_token)

    return {
        "status": "success",
        "message": "Token pair refreshed successfully.",
        "user": UserResponse.model_validate(user),
    }


@router.post("/logout")
async def logout(response: Response):
    """Clears HttpOnly authentication cookies."""
    clear_auth_cookies(response)
    return {"status": "success", "message": "Successfully logged out. Cookies cleared."}


@router.post("/sso/callback")
async def sso_callback(
    claims: OIDCClaims,
    response: Response,
    session: AsyncSession = Depends(get_db),
):
    """
    OIDC / SAML SSO claim intake endpoint.
    Executes Just-In-Time (JIT) Tenant Provisioning within an async transaction:
    - Root tenant creation (if domain is new)
    - Folder (department) descent
    - Project (enrolled programs) descent
    - Leaf Resource node attachment and User mapping
    - Sets 15-minute access token & 7-day refresh token HttpOnly cookies.
    """
    user, resource_node = await JITProvisioner.provision_user_and_hierarchy(session, claims)
    await session.commit()

    access_token = create_access_token(str(user.id), user.email, user.roles)
    refresh_token = create_refresh_token(str(user.id))

    set_auth_cookies(response, access_token, refresh_token)

    return {
        "status": "success",
        "message": "JIT tenant hierarchy provisioned and user authenticated.",
        "user": UserResponse.model_validate(user),
        "provisioned_resource_node": {
            "id": str(resource_node.id),
            "name": resource_node.name,
            "path": resource_node.path,
            "tier": resource_node.visibility_settings.get("tier"),
        },
    }


@router.post("/mock-sso")
async def mock_sso_login(
    preset: str = "stanford_faculty",  # 'stanford_faculty' | 'acme_executive' | 'student'
    response: Response = None,
    session: AsyncSession = Depends(get_db),
):
    """
    Developer convenience endpoint simulating enterprise IdP SAML/OIDC assertions.
    """
    presets = {
        "stanford_faculty": OIDCClaims(
            sub="sso-id-prof-smith-9921",
            email="dr.smith@stanford.edu",
            full_name="Dr. Eleanor Smith",
            organization_domain="stanford.edu",
            department="School of Engineering",
            roles=["faculty", "phd_advisor"],
            enrolled_programs=["PhD Advising", "Robotics Research Group"],
            capacity_title="Professor & Graduate Advisor",
        ),
        "acme_executive": OIDCClaims(
            sub="sso-id-exec-vance-4412",
            email="alex.vance@acmecorp.com",
            full_name="Alex Vance (EVP Strategy)",
            organization_domain="acmecorp.com",
            department="Executive Leadership",
            roles=["executive", "c-level", "admin"],
            enrolled_programs=["Strategic M&A Advisory"],
            capacity_title="EVP of Corporate Strategy",
        ),
        "student": OIDCClaims(
            sub="sso-id-student-lee-1120",
            email="sarah.lee@stanford.edu",
            full_name="Sarah Lee",
            organization_domain="stanford.edu",
            department="School of Engineering",
            roles=["student"],
            enrolled_programs=["Undergraduate Mentorship"],
            capacity_title="Student Researcher",
        ),
    }

    claim = presets.get(preset, presets["stanford_faculty"])
    return await sso_callback(claim, response, session)


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Returns current authenticated identity and all mapped operational capacities (Resource nodes).
    Demonstrates Identity vs Capacity separation.
    """
    stmt = (
        select(NodeUserMapping, Node)
        .join(Node, NodeUserMapping.node_id == Node.id)
        .where(NodeUserMapping.user_id == current_user.id)
    )
    res = await session.execute(stmt)
    pairs = res.all()

    capacities: list[ResourceNodeBrief] = []
    for mapping, node in pairs:
        v_settings = node.visibility_settings or {}
        capacities.append(
            ResourceNodeBrief(
                node_id=node.id,
                tenant_id=node.tenant_id,
                name=node.name,
                path=node.path,
                capacity_title=mapping.capacity_title,
                tier=v_settings.get("tier", "PUBLIC"),
            )
        )

    return MeResponse(
        user=UserResponse.model_validate(current_user),
        active_capacities=capacities,
    )
