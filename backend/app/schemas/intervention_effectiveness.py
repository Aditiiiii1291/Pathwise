from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field

EFFECTIVENESS_DISCLAIMER = (
    "Observed changes describe student risk assessments over time and do not "
    "establish that an intervention caused the change."
)


class SnapshotContext(BaseModel):
    snapshot_id: Optional[int] = None
    score: float
    risk_tier: str
    trend: str
    computed_at: datetime


class InterventionEffectivenessDetail(BaseModel):
    intervention_id: int
    student_id: int
    student_name: Optional[str] = None
    title: str
    intervention_type: str
    status: str
    created_at: datetime
    classification: str = Field(
        ...,
        description="IMPROVED, STABLE, WORSENED, AWAITING_REASSESSMENT, or INSUFFICIENT_DATA"
    )
    before: Optional[SnapshotContext] = None
    after: Optional[SnapshotContext] = None
    score_delta: Optional[float] = None
    tier_transition: Optional[str] = None
    trend_transition: Optional[str] = None
    interpretation: str
    disclaimer: str = EFFECTIVENESS_DISCLAIMER


class InterventionEffectivenessSummaryItem(BaseModel):
    intervention_id: int
    classification: str
    score_delta: Optional[float] = None
    before_score: Optional[float] = None
    after_score: Optional[float] = None
    before_tier: Optional[str] = None
    after_tier: Optional[str] = None
    interpretation: str


class AggregateEffectivenessSummary(BaseModel):
    total_interventions: int
    evaluated_interventions: int
    improved_count: int
    stable_count: int
    worsened_count: int
    awaiting_reassessment_count: int
    insufficient_data_count: int
    average_score_change: Optional[float] = None
    disclaimer: str = EFFECTIVENESS_DISCLAIMER


class FollowUpItem(BaseModel):
    intervention_id: int
    student_id: int
    student_name: Optional[str] = None
    student_roll: Optional[str] = None
    student_dept: Optional[str] = None
    title: str
    intervention_type: str
    status: str
    follow_up_date: Optional[date] = None
    follow_up_state: str = Field(
        ...,
        description="OVERDUE, DUE_TODAY, UPCOMING, CLOSED, or NO_FOLLOW_UP"
    )
    days_until_due: Optional[int] = None
    created_at: datetime


class PaginatedFollowUpResponse(BaseModel):
    items: List[FollowUpItem]
    page: int
    page_size: int
    total: int
    pages: int
    overdue_count: int
    due_today_count: int
    upcoming_count: int
