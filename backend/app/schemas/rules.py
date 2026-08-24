from typing import List, Optional, Dict
from pydantic import BaseModel, Field, model_validator

class RuleWeights(BaseModel):
    attendance: float = Field(default=0.30, ge=0.0, le=1.0, description="Weight for attendance factor")
    marks: float = Field(default=0.25, ge=0.0, le=1.0, description="Weight for academic marks factor")
    backlogs: float = Field(default=0.15, ge=0.0, le=1.0, description="Weight for backlogs and attempts factor")
    fees: float = Field(default=0.10, ge=0.0, le=1.0, description="Weight for contextual fees factor")
    trends: float = Field(default=0.20, ge=0.0, le=1.0, description="Weight for multi-domain temporal trends factor")

    @model_validator(mode="after")
    def validate_sum(self) -> "RuleWeights":
        total = self.attendance + self.marks + self.backlogs + self.fees + self.trends
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"Rule weights must sum to exactly 1.0 (got {total:.4f})")
        return self

class RuleThresholds(BaseModel):
    attendance_min: float = Field(default=75.0, description="Minimum acceptable attendance percentage")
    attendance_slope_min: float = Field(default=-5.0, description="Slope threshold for rapid attendance decline (pp/week)")
    attendance_decline_max: float = Field(default=10.0, description="Maximum acceptable percentage points lost from peak")
    attendance_consecutive_decline_max: int = Field(default=3, description="Consecutive declining weeks threshold")

    marks_min: float = Field(default=40.0, description="Minimum passing marks percentage")
    marks_slope_min: float = Field(default=-5.0, description="Slope threshold for marks deterioration (pp/stage)")
    marks_decline_max: float = Field(default=15.0, description="Maximum acceptable marks percentage points lost from peak")
    consecutive_failures_max: int = Field(default=2, description="Consecutive failing assessment stages threshold")
    failed_subjects_max: int = Field(default=1, description="Maximum allowed currently failing distinct subjects")

    active_backlogs_max: int = Field(default=2, description="Threshold count of active backlogs")
    fee_overdue_terms_max: int = Field(default=1, description="Threshold count of overdue fee terms")

class RuleEngineConfig(BaseModel):
    weights: RuleWeights = Field(default_factory=RuleWeights)
    thresholds: RuleThresholds = Field(default_factory=RuleThresholds)
    department: Optional[str] = Field(default=None, description="Optional department-specific override")

class TriggeredRule(BaseModel):
    code: str = Field(..., description="Stable programmatic identifier for the rule")
    factor: str = Field(..., description="Category: attendance, marks, backlogs, fees, trends")
    feature: str = Field(..., description="Specific feature triggering the rule")
    observed_value: float = Field(..., description="Actual measured value from student features")
    threshold: float = Field(..., description="Configured rule threshold")
    message: str = Field(..., description="Factual, supportive, non-stigmatizing explanation")

class FactorScores(BaseModel):
    attendance: float = Field(..., ge=0.0, le=100.0)
    marks: float = Field(..., ge=0.0, le=100.0)
    backlogs: float = Field(..., ge=0.0, le=100.0)
    fees: float = Field(..., ge=0.0, le=100.0)
    trends: float = Field(..., ge=0.0, le=100.0)

class FactorContributions(BaseModel):
    attendance: float = Field(..., ge=0.0, le=100.0)
    marks: float = Field(..., ge=0.0, le=100.0)
    backlogs: float = Field(..., ge=0.0, le=100.0)
    fees: float = Field(..., ge=0.0, le=100.0)
    trends: float = Field(..., ge=0.0, le=100.0)

class RuleEvaluationResult(BaseModel):
    student_id: int
    rule_score: float = Field(..., ge=0.0, le=100.0, description="Overall weighted deterministic concern score (0-100)")
    factor_scores: FactorScores
    factor_contributions: FactorContributions
    triggered_rules: List[TriggeredRule] = Field(default_factory=list)
