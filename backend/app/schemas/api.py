from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

try:
    from app.schemas.student import UnifiedStudentProfile
    from app.schemas.risk import RiskFusionResult
    from app.schemas.explanation import ExplanationResult
    from app.schemas.rules import RuleWeights, RuleThresholds, RuleEngineConfig
except ImportError:
    from backend.app.schemas.student import UnifiedStudentProfile
    from backend.app.schemas.risk import RiskFusionResult
    from backend.app.schemas.explanation import ExplanationResult
    from backend.app.schemas.rules import RuleWeights, RuleThresholds, RuleEngineConfig

class StudentListItem(BaseModel):
    id: int
    roll_number: str
    name: str
    department: str
    semester: int
    enrollment_year: Optional[int] = None
    mentor_name: Optional[str] = None
    latest_final_score: Optional[float] = None
    latest_risk_tier: Optional[str] = None
    latest_trend: Optional[str] = None
    latest_assessment_date: Optional[datetime] = None

class PaginatedStudentResponse(BaseModel):
    items: List[StudentListItem]
    page: int
    page_size: int
    total: int
    pages: int

class StudentProfileDetailResponse(BaseModel):
    profile: UnifiedStudentProfile
    latest_assessment: Optional[RiskFusionResult] = None
    latest_explanation: Optional[ExplanationResult] = None

class StudentAssessmentResponse(BaseModel):
    student_id: int
    assessment: RiskFusionResult
    explanation: ExplanationResult

class DashboardOverviewResponse(BaseModel):
    total_students: int
    assessed_students: int
    risk_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    )
    trend_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"IMPROVING": 0, "STABLE": 0, "GRADUALLY_DETERIORATING": 0, "RAPIDLY_DETERIORATING": 0}
    )
    average_final_score: float = 0.0

class DepartmentSummaryItem(BaseModel):
    department: str
    student_count: int
    at_risk_count: int
    critical_count: int
    average_final_score: float = 0.0

class RuleConfigUpdate(BaseModel):
    department: Optional[str] = None
    weights: RuleWeights
    thresholds: RuleThresholds
