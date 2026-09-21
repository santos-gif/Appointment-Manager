import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OIDCClaims(BaseModel):
    """
    Standard claims extracted from enterprise OIDC / SAML SSO assertions.
    """
    sub: str = Field(description="Unique subject identifier from IdP")
    email: EmailStr
    full_name: str
    organization_domain: str = Field(description="Domain used to determine tenant root node, e.g. stanford.edu")
    department: str = Field(description="Department mapping to Folder node, e.g. School of Engineering")
    roles: List[str] = Field(default_factory=list, description="Roles list, e.g. ['faculty', 'researcher']")
    enrolled_programs: List[str] = Field(default_factory=list, description="Programs mapping to Project nodes, e.g. ['PhD Advising']")
    capacity_title: Optional[str] = Field(default=None, description="Host operational capacity title")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    roles: List[str]
    is_active: bool
    is_superuser: bool


class ResourceNodeBrief(BaseModel):
    node_id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    path: str
    capacity_title: str
    tier: str


class MeResponse(BaseModel):
    user: UserResponse
    active_capacities: List[ResourceNodeBrief]
