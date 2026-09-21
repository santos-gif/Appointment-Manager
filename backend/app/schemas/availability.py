import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AvailabilityRuleCreate(BaseModel):
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="0=Monday, 6=Sunday")
    specific_date: Optional[date] = Field(None, description="One-off specific date override")
    start_time: str = Field("09:00", pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    end_time: str = Field("17:00", pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    slot_duration_minutes: int = Field(30, ge=5, le=480)
    buffer_minutes: int = Field(10, ge=0, le=120)
    is_active: bool = True


class AvailabilityRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    node_id: uuid.UUID
    day_of_week: Optional[int]
    specific_date: Optional[date]
    start_time: str
    end_time: str
    slot_duration_minutes: int
    buffer_minutes: int
    is_active: bool
    created_at: datetime


class NodeAvailabilityMatrixResponse(BaseModel):
    node_id: uuid.UUID
    rules: List[AvailabilityRuleResponse]
