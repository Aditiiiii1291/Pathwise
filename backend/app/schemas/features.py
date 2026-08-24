from typing import Dict, Optional
from pydantic import BaseModel, Field

class StudentFeatures(BaseModel):
    student_id: int
    
    # Attendance Features
    attendance_current: float = Field(..., description="Latest recorded attendance percentage (0.0-100.0)")
    attendance_mean: float = Field(..., description="Historical mean attendance percentage (0.0-100.0)")
    attendance_slope: float = Field(..., description="Linear slope of attendance across chronological weeks (pp/week)")
    attendance_decline_pp: float = Field(..., description="Percentage points lost from historical peak to current (>= 0.0)")
    attendance_recent_vs_historical: float = Field(..., description="Ratio of recent attendance (last 2 periods) to historical periods")
    attendance_consecutive_decline: int = Field(..., description="Count of consecutive declining transitions moving backwards from latest")
    attendance_acceleration: float = Field(..., description="Rate of change of weekly attendance differences (second derivative)")
    attendance_history_count: int = Field(..., description="Number of weekly attendance observations")
    has_sufficient_attendance_history: bool = Field(..., description="True if student has >= 3 attendance observations")

    # Marks Features
    marks_current_avg: float = Field(..., description="Average normalized percentage in the most recent assessment stage (0.0-100.0)")
    marks_mean: float = Field(..., description="Overall mean normalized marks percentage (0.0-100.0)")
    marks_slope: float = Field(..., description="Linear trend of normalized marks across sequential assessments (pp/stage)")
    marks_decline_pp: float = Field(..., description="Percentage points lost from historical peak assessment to current (>= 0.0)")
    marks_recent_vs_previous: float = Field(..., description="Ratio of latest assessment average to earlier assessments")
    marks_consecutive_failures: int = Field(..., description="Number of consecutive recent assessment stages below pass threshold (40%)")
    marks_failed_subject_count: int = Field(..., description="Number of distinct subjects currently failing in latest assessment")
    marks_history_count: int = Field(..., description="Number of assessment marks records")
    has_sufficient_marks_history: bool = Field(..., description="True if student has >= 2 assessment observations")

    # Backlog & Attempt Features
    backlog_count_active: int = Field(..., description="Total count of active uncleared backlogs")
    backlog_count_total: int = Field(..., description="Total historical backlog/attempt entries")
    backlog_new_this_semester: int = Field(..., description="Active backlogs associated with current semester")
    backlog_trend_numeric: int = Field(..., description="Backlog trajectory direction: -1 decreasing, 0 stable, +1 increasing")
    max_attempt_number: int = Field(..., description="Highest examination attempt number on record")

    # Contextual Fee Features (Non-causal)
    fee_status_latest: str = Field(..., description="Latest fee status: PAID, PARTIAL, PENDING, or UNKNOWN")
    fee_percentage_paid: float = Field(..., description="Percentage of fee paid for latest term (0.0-100.0)")
    fee_terms_overdue: int = Field(..., description="Number of terms with unpaid fees past due date relative to reference date")
    fee_pending_count: int = Field(..., description="Total count of PARTIAL or PENDING fee records")

    # Subject-level slope breakdown (Optional extra detail)
    subject_slopes: Dict[str, float] = Field(default_factory=dict, description="Detailed regression slopes by subject")
