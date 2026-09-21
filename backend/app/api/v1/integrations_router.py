import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.database import get_db
from app.models.integrations import CalendarIntegration, IntakeFormSchema, PaymentEscrowConfig
from app.models.node import Node
from app.models.user import User
from app.schemas.integrations import (
    CalendarIntegrationResponse,
    IntakeFormSchemaCreate,
    IntakeFormSchemaResponse,
    PaymentEscrowConfigSchema,
)

router = APIRouter(prefix="/integrations", tags=["Integrations & Operational Tools"])


@router.get("/calendar/{resource_node_id}", response_model=List[CalendarIntegrationResponse])
async def get_calendar_sync_status(
    resource_node_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    """Returns external calendar sync integrations (Google / Outlook) for a host node."""
    stmt = select(CalendarIntegration).where(CalendarIntegration.resource_node_id == resource_node_id)
    res = await session.execute(stmt)
    integrations = res.scalars().all()

    if not integrations:
        # Default mock active integrations for UI demonstration
        return [
            CalendarIntegrationResponse(
                id=uuid.uuid4(),
                resource_node_id=resource_node_id,
                provider="google",
                account_email="host.calendar@gmail.com",
                sync_active=True,
                last_synced_at=datetime.now(timezone.utc),
                sync_status_message="Google Calendar Real-Time Busy Slots Synchronized",
            ),
            CalendarIntegrationResponse(
                id=uuid.uuid4(),
                resource_node_id=resource_node_id,
                provider="outlook",
                account_email="host.enterprise@outlook.com",
                sync_active=False,
                last_synced_at=None,
                sync_status_message="OAuth Authorization Pending",
            ),
        ]

    return [CalendarIntegrationResponse.model_validate(i) for i in integrations]


@router.post("/calendar/{resource_node_id}/connect")
async def trigger_calendar_oauth(
    resource_node_id: uuid.UUID,
    provider: str,  # 'google' | 'outlook'
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Simulates initiating and completing OAuth handshake for Google / Outlook calendar sync."""
    stmt = select(CalendarIntegration).where(
        CalendarIntegration.resource_node_id == resource_node_id,
        CalendarIntegration.provider == provider,
    )
    res = await session.execute(stmt)
    rec = res.scalar_one_or_none()

    if not rec:
        rec = CalendarIntegration(
            id=uuid.uuid4(),
            resource_node_id=resource_node_id,
            provider=provider,
            account_email=current_user.email,
            sync_active=True,
            last_synced_at=datetime.now(timezone.utc),
            sync_status_message=f"{provider.capitalize()} Calendar Connected & Syncing",
        )
        session.add(rec)
    else:
        rec.sync_active = True
        rec.last_synced_at = datetime.now(timezone.utc)
        rec.sync_status_message = f"{provider.capitalize()} Calendar Reconnected"

    await session.commit()
    return {"status": "success", "message": f"{provider.capitalize()} Calendar successfully synchronized."}


@router.get("/escrow/{node_id}", response_model=PaymentEscrowConfigSchema)
async def get_escrow_config(
    node_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    stmt = select(PaymentEscrowConfig).where(PaymentEscrowConfig.node_id == node_id)
    res = await session.execute(stmt)
    cfg = res.scalar_one_or_none()
    if not cfg:
        return PaymentEscrowConfigSchema(
            node_id=node_id,
            provider="stripe",
            is_enabled=False,
            amount_cents=0,
            currency="USD",
            escrow_policy="escrow_hold_until_session",
        )
    return PaymentEscrowConfigSchema.model_validate(cfg)


@router.put("/escrow/{node_id}", response_model=PaymentEscrowConfigSchema)
async def update_escrow_config(
    node_id: uuid.UUID,
    payload: PaymentEscrowConfigSchema,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(PaymentEscrowConfig).where(PaymentEscrowConfig.node_id == node_id)
    res = await session.execute(stmt)
    cfg = res.scalar_one_or_none()

    if not cfg:
        cfg = PaymentEscrowConfig(
            id=uuid.uuid4(),
            node_id=node_id,
            provider=payload.provider,
            is_enabled=payload.is_enabled,
            amount_cents=payload.amount_cents,
            currency=payload.currency,
            escrow_policy=payload.escrow_policy,
            account_connected_id=payload.account_connected_id,
        )
        session.add(cfg)
    else:
        cfg.provider = payload.provider
        cfg.is_enabled = payload.is_enabled
        cfg.amount_cents = payload.amount_cents
        cfg.currency = payload.currency
        cfg.escrow_policy = payload.escrow_policy
        cfg.account_connected_id = payload.account_connected_id

    await session.commit()
    return PaymentEscrowConfigSchema.model_validate(cfg)


@router.get("/intake-schema/{node_id}", response_model=Optional[IntakeFormSchemaResponse])
async def get_intake_schema(
    node_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    stmt = select(IntakeFormSchema).where(IntakeFormSchema.node_id == node_id)
    res = await session.execute(stmt)
    schema = res.scalar_one_or_none()
    if not schema:
        # Default mock schema
        return IntakeFormSchemaResponse(
            id=uuid.uuid4(),
            node_id=node_id,
            title="Standard Engagement Questionnaire",
            description="Please specify the purpose of your appointment.",
            fields_json=[
                {"id": "q1", "type": "text", "label": "Meeting Objective / Subject", "required": True},
                {"id": "q2", "type": "select", "label": "Topic Category", "options": ["Research", "Strategy", "Administrative", "Other"], "required": True},
                {"id": "q3", "type": "textarea", "label": "Brief Agenda or Pre-Reading Links", "required": False},
            ],
            created_at=datetime.now(timezone.utc),
        )
    return IntakeFormSchemaResponse.model_validate(schema)


@router.put("/intake-schema/{node_id}", response_model=IntakeFormSchemaResponse)
async def save_intake_schema(
    node_id: uuid.UUID,
    payload: IntakeFormSchemaCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(IntakeFormSchema).where(IntakeFormSchema.node_id == node_id)
    res = await session.execute(stmt)
    schema = res.scalar_one_or_none()

    fields_data = [f.model_dump() for f in payload.fields]

    if not schema:
        schema = IntakeFormSchema(
            id=uuid.uuid4(),
            node_id=node_id,
            title=payload.title,
            description=payload.description,
            fields_json=fields_data,
        )
        session.add(schema)
    else:
        schema.title = payload.title
        schema.description = payload.description
        schema.fields_json = fields_data

    await session.commit()
    return IntakeFormSchemaResponse.model_validate(schema)
