import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CalendarIntegrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resource_node_id: uuid.UUID
    provider: str
    account_email: str
    sync_active: bool
    last_synced_at: Optional[datetime]
    sync_status_message: str


class PaymentEscrowConfigSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[uuid.UUID] = None
    node_id: uuid.UUID
    provider: str = "stripe"
    is_enabled: bool = False
    amount_cents: int = Field(0, ge=0)
    currency: str = "USD"
    escrow_policy: str = "escrow_hold_until_session"
    account_connected_id: Optional[str] = None


class IntakeFieldSchema(BaseModel):
    id: str
    type: str = Field(description="'text', 'textarea', 'select', 'number', 'checkbox'")
    label: str
    placeholder: Optional[str] = None
    required: bool = True
    options: List[str] = Field(default_factory=list, description="Options if type is select")


class IntakeFormSchemaCreate(BaseModel):
    node_id: uuid.UUID
    title: str
    description: Optional[str] = None
    fields: List[IntakeFieldSchema]


class IntakeFormSchemaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    node_id: uuid.UUID
    title: str
    description: Optional[str]
    fields_json: List[Dict[str, Any]]
    created_at: datetime
