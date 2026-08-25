from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

try:
    from app.models.intervention import InterventionTypeEnum, InterventionStatusEnum
except ImportError:
    from backend.app.models.intervention import InterventionTypeEnum, InterventionStatusEnum


class InterventionCreate(BaseModel):
    student_id: int = Field(..., description="Target student ID")
    mentor_id: Optional[int] = Field(None, description="Assigned mentor ID (optional)")
    intervention_type: InterventionTypeEnum = Field(
        default=InterventionTypeEnum.COUNSELLING,
        description="Type of intervention/counselling"
    )
    title: str = Field(..., min_length=1, max_length=255, description="Brief intervention title")
    notes: Optional[str] = Field(None, max_length=5000, description="Counselling and action notes")
    status: InterventionStatusEnum = Field(
        default=InterventionStatusEnum.PLANNED,
        description="Initial workflow status"
    )
    follow_up_date: Optional[date] = Field(None, description="Optional scheduled follow-up date (YYYY-MM-DD)")

    @field_validator("title")
    @classmethod
    def validate_title_non_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Intervention title cannot be empty or whitespace only.")
        return trimmed


class InterventionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated title")
    intervention_type: Optional[InterventionTypeEnum] = Field(None, description="Updated intervention type")
    notes: Optional[str] = Field(None, max_length=5000, description="Updated notes")
    status: Optional[InterventionStatusEnum] = Field(None, description="Updated workflow status")
    follow_up_date: Optional[date] = Field(None, description="Updated follow-up date (YYYY-MM-DD)")
    mentor_id: Optional[int] = Field(None, description="Updated mentor ID")

    @field_validator("title")
    @classmethod
    def validate_title_non_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Intervention title cannot be empty or whitespace only.")
            return trimmed
        return v


class InterventionItem(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    student_roll: Optional[str] = None
    student_dept: Optional[str] = None
    mentor_id: Optional[int] = None
    mentor_name: Optional[str] = None
    intervention_type: str
    title: str
    notes: Optional[str] = None
    status: str
    follow_up_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_follow_up_due: bool = False

    model_config = {"from_attributes": True}


class PaginatedInterventionResponse(BaseModel):
    items: List[InterventionItem]
    page: int
    page_size: int
    total: int
    pages: int


class InterventionSummaryResponse(BaseModel):
    total_interventions: int
    active_count: int
    planned_count: int
    completed_count: int
    cancelled_count: int
    follow_ups_due_count: int
