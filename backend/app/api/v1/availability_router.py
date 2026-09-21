import uuid
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_optional_current_user
from app.database import get_db
from app.models.availability import NodeAvailability
from app.models.node import Node
from app.models.user import User
from app.schemas.availability import AvailabilityRuleCreate, AvailabilityRuleResponse, NodeAvailabilityMatrixResponse
from app.schemas.booking import AvailableSlot
from app.services.scheduling_service import SchedulingService

router = APIRouter(prefix="/availability", tags=["Operational Capacity & Availability"])


@router.get("/{node_id}", response_model=NodeAvailabilityMatrixResponse)
async def get_node_availability(
    node_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    """Retrieves the active availability rules matrix for a node context."""
    stmt = select(NodeAvailability).where(NodeAvailability.node_id == node_id).order_by(NodeAvailability.day_of_week)
    res = await session.execute(stmt)
    rules = res.scalars().all()
    return NodeAvailabilityMatrixResponse(
        node_id=node_id,
        rules=[AvailabilityRuleResponse.model_validate(r) for r in rules],
    )


@router.put("/{node_id}", response_model=NodeAvailabilityMatrixResponse)
async def update_node_availability_matrix(
    node_id: uuid.UUID,
    rules: List[AvailabilityRuleCreate],
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Updates the availability rules matrix for a host's operational capacity node.
    Built to handle inputs from the Angular Reactive Form matrix.
    """
    node = await session.get(Node, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Resource node not found.")

    # Remove existing rules and replace atomically
    await session.execute(delete(NodeAvailability).where(NodeAvailability.node_id == node_id))

    new_rule_records = []
    for r in rules:
        rec = NodeAvailability(
            id=uuid.uuid4(),
            node_id=node_id,
            day_of_week=r.day_of_week,
            specific_date=r.specific_date,
            start_time=r.start_time,
            end_time=r.end_time,
            slot_duration_minutes=r.slot_duration_minutes,
            buffer_minutes=r.buffer_minutes,
            is_active=r.is_active,
        )
        session.add(rec)
        new_rule_records.append(rec)

    await session.commit()
    return NodeAvailabilityMatrixResponse(
        node_id=node_id,
        rules=[AvailabilityRuleResponse.model_validate(r) for r in new_rule_records],
    )


@router.get("/{node_id}/slots", response_model=List[AvailableSlot])
async def get_available_slots(
    node_id: uuid.UUID,
    target_date: Optional[str] = Query(None, description="YYYY-MM-DD format"),
    timezone: str = Query("UTC", description="Booker's local IANA timezone e.g. America/New_York"),
    session: AsyncSession = Depends(get_db),
):
    """
    Global Timezone Engine endpoint:
    Calculates conflict-free available slots for target date adjusted for booker's timezone and DST.
    """
    if not target_date:
        d = date.today()
    else:
        try:
            d = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    slots = await SchedulingService.compute_available_slots(
        session=session,
        resource_node_id=node_id,
        target_date=d,
        booker_tz_str=timezone,
    )
    return slots
