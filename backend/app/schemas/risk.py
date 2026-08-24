from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator

class FusionConfig(BaseModel):
    rule_weight: float = Field(default=0.5, ge=0.0, le=1.0, description="Weight assigned to rule engine score")
    ml_weight: float = Field(default=0.5, ge=0.0, le=1.0, description="Weight assigned to ML dropout probability score")

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "FusionConfig":
        total = self.rule_weight + self.ml_weight
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"Fusion weights must sum to exactly 1.0 (got {total:.4f})")
        return self

class RiskFusionResult(BaseModel):
    student_id: int
    rule_score: float = Field(..., ge=0.0, le=100.0, description="Deterministic rule engine score (0.0-100.0)")
    ml_probability: float = Field(..., ge=0.0, le=1.0, description="Predicted dropout probability from ML model (0.0-1.0)")
    ml_score: float = Field(..., ge=0.0, le=100.0, description="Rescaled ML probability score (ml_probability * 100.0)")
    rule_weight: float = Field(..., ge=0.0, le=1.0, description="Weight applied to rule_score")
    ml_weight: float = Field(..., ge=0.0, le=1.0, description="Weight applied to ml_score")
    final_score: float = Field(..., ge=0.0, le=100.0, description="Fused final retention risk score (0.0-100.0)")
    risk_tier: str = Field(..., description="Continuous risk tier: LOW, MEDIUM, HIGH, CRITICAL")
    trend: str = Field(..., description="Temporal progression: RAPIDLY_DETERIORATING, GRADUALLY_DETERIORATING, STABLE, IMPROVING")
    computed_at: Optional[datetime] = Field(default=None, description="Timezone-aware evaluation timestamp")
