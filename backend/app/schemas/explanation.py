from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class ExplanationFactor(BaseModel):
    code: str = Field(..., description="Stable programmatic identifier for the factor")
    category: str = Field(..., description="High-level category: ATTENDANCE, ACADEMICS, BACKLOG, FEES, TREND")
    title: str = Field(..., description="Concise human-readable factor title")
    description: str = Field(..., description="Factual description referencing observed values")
    severity: str = Field(..., description="Severity level: HIGH, MODERATE, LOW, INFO")
    observed_value: Optional[Union[float, str]] = Field(default=None, description="Actual student metric")
    reference_value: Optional[Union[float, str]] = Field(default=None, description="Institutional threshold or comparison benchmark")
    source: str = Field(default="RULE", description="Signal provenance: RULE, FEATURE")

class Recommendation(BaseModel):
    code: str = Field(..., description="Programmatic action code")
    category: str = Field(..., description="Action category: ATTENDANCE, ACADEMICS, BACKLOG, ADMINISTRATIVE, COORDINATION")
    title: str = Field(..., description="Action headline for mentor or advisor")
    description: str = Field(..., description="Actionable, non-judgmental guidance")
    priority: str = Field(..., description="Priority level: HIGH, MEDIUM, LOW")

class GlobalMLContext(BaseModel):
    disclaimer: str = Field(
        default=(
            "The current prediction model was trained on synthetic development data and is intended for "
            "demonstration/testing. Institutional deployment requires validation using appropriate historical data."
        ),
        description="Synthetic training data notice",
    )
    top_global_features: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Global model feature importances (NOT per-student attribution)",
    )

class ExplanationResult(BaseModel):
    student_id: int
    risk_tier: str = Field(..., description="Continuous risk tier: LOW, MEDIUM, HIGH, CRITICAL")
    trend: str = Field(..., description="Temporal progression: RAPIDLY_DETERIORATING, GRADUALLY_DETERIORATING, STABLE, IMPROVING")
    final_score: float = Field(..., ge=0.0, le=100.0, description="Fused final retention risk score")
    rule_score: float = Field(..., ge=0.0, le=100.0, description="Deterministic rule score")
    ml_probability: float = Field(..., ge=0.0, le=1.0, description="Predicted dropout probability (0.0-1.0)")
    summary: str = Field(..., description="Synthesized executive risk and trajectory summary")
    top_factors: List[ExplanationFactor] = Field(default_factory=list, description="Ranked student-specific factual concerns")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Ranked actionable supportive guidance")
    global_ml_context: Optional[GlobalMLContext] = Field(default=None, description="Global model context and synthetic disclaimer")
    generated_at: Optional[datetime] = Field(default=None, description="Timezone-aware generation timestamp")
