from datetime import datetime, timezone
from typing import Optional, Dict, Any

try:
    from app.schemas.features import StudentFeatures
    from app.schemas.risk import FusionConfig, RiskFusionResult
    from app.models.risk import RiskSnapshot, RiskTierEnum, TrendEnum
except ImportError:
    from backend.app.schemas.features import StudentFeatures
    from backend.app.schemas.risk import FusionConfig, RiskFusionResult
    from backend.app.models.risk import RiskSnapshot, RiskTierEnum, TrendEnum

class RiskFusionEngine:
    """
    Combines deterministic rule_score and ML predicted dropout_probability into
    a unified risk assessment (final_score, risk_tier, trend).
    """

    # Continuous Risk Tier Boundaries
    # LOW:      0.0  <= score < 25.0
    # MEDIUM:  25.0  <= score < 50.0
    # HIGH:    50.0  <= score < 75.0
    # CRITICAL: 75.0 <= score <= 100.0
    TIER_MEDIUM_MIN = 25.0
    TIER_HIGH_MIN = 50.0
    TIER_CRITICAL_MIN = 75.0

    # Trend Threshold Constants (based on Phase 6 feature units)
    RAPID_ATT_SLOPE = -5.0
    RAPID_MARKS_SLOPE = -6.0
    GRADUAL_ATT_SLOPE = -1.5
    GRADUAL_MARKS_SLOPE = -2.0
    IMPROVEMENT_ATT_SLOPE = 1.5
    IMPROVEMENT_MARKS_SLOPE = 2.0

    @classmethod
    def fuse(
        cls,
        student_id: int,
        rule_score: float,
        ml_probability: float,
        features: StudentFeatures,
        config: Optional[FusionConfig] = None,
    ) -> RiskFusionResult:
        """
        Executes risk fusion combining rule and ML indicators.
        """
        if config is None:
            config = FusionConfig()

        # Strict input validation
        if rule_score < 0.0 or rule_score > 100.0:
            raise ValueError(f"rule_score must be between 0.0 and 100.0 (got {rule_score})")
        if ml_probability < 0.0 or ml_probability > 1.0:
            raise ValueError(f"ml_probability must be between 0.0 and 1.0 (got {ml_probability})")

        # Mathematical Fusion
        ml_score = ml_probability * 100.0
        raw_final_score = (config.rule_weight * rule_score) + (config.ml_weight * ml_score)
        
        # Classification MUST occur on raw unrounded score before display rounding
        risk_tier = cls._determine_risk_tier(raw_final_score)
        trend = cls._determine_trend(features)

        rounded_final_score = round(min(100.0, max(0.0, raw_final_score)), 2)

        return RiskFusionResult(
            student_id=student_id,
            rule_score=round(rule_score, 2),
            ml_probability=round(ml_probability, 4),
            ml_score=round(ml_score, 2),
            rule_weight=config.rule_weight,
            ml_weight=config.ml_weight,
            final_score=rounded_final_score,
            risk_tier=risk_tier,
            trend=trend,
            computed_at=datetime.now(timezone.utc),
        )

    @classmethod
    def _determine_risk_tier(cls, raw_score: float) -> str:
        """Assigns continuous, gap-free risk tier based on raw numerical score."""
        if raw_score < cls.TIER_MEDIUM_MIN:
            return "LOW"
        elif raw_score < cls.TIER_HIGH_MIN:
            return "MEDIUM"
        elif raw_score < cls.TIER_CRITICAL_MIN:
            return "HIGH"
        else:
            return "CRITICAL"

    @classmethod
    def _determine_trend(cls, features: StudentFeatures) -> str:
        """
        Determines temporal trend strictly from Phase 6 temporal features.
        Precedence:
          1. RAPIDLY_DETERIORATING
          2. GRADUALLY_DETERIORATING
          3. IMPROVING
          4. STABLE
        """
        att_slope = features.attendance_slope
        marks_slope = features.marks_slope
        att_acc = features.attendance_acceleration
        att_consec = features.attendance_consecutive_decline
        marks_failures = features.marks_consecutive_failures
        att_decline = features.attendance_decline_pp
        marks_decline = features.marks_decline_pp
        backlog_trend = features.backlog_trend_numeric

        has_att_hist = features.has_sufficient_attendance_history
        has_marks_hist = features.has_sufficient_marks_history

        # 1. Check RAPIDLY_DETERIORATING
        is_rapid = False
        if has_att_hist and att_slope <= cls.RAPID_ATT_SLOPE and (att_acc <= -0.5 or att_consec >= 3 or att_decline >= 20.0):
            is_rapid = True
        elif has_att_hist and att_slope <= -8.0:
            is_rapid = True
        elif has_marks_hist and marks_slope <= -8.0:
            is_rapid = True
        elif has_marks_hist and marks_slope <= cls.RAPID_MARKS_SLOPE and (marks_failures >= 2 or marks_decline >= 20.0):
            is_rapid = True
        elif has_att_hist and has_marks_hist and att_slope <= -4.0 and marks_slope <= -4.0:
            is_rapid = True

        if is_rapid:
            return "RAPIDLY_DETERIORATING"

        # 2. Check GRADUALLY_DETERIORATING
        is_gradual = False
        if has_att_hist and att_slope <= cls.GRADUAL_ATT_SLOPE:
            is_gradual = True
        elif has_marks_hist and marks_slope <= cls.GRADUAL_MARKS_SLOPE:
            is_gradual = True
        elif att_consec >= 2:
            is_gradual = True
        elif att_decline >= 12.0 or marks_decline >= 15.0:
            is_gradual = True
        elif backlog_trend == 1:
            is_gradual = True

        if is_gradual:
            return "GRADUALLY_DETERIORATING"

        # 3. Check IMPROVING
        is_improving = False
        has_positive_signal = (
            (has_att_hist and att_slope >= cls.IMPROVEMENT_ATT_SLOPE)
            or (has_marks_hist and marks_slope >= cls.IMPROVEMENT_MARKS_SLOPE)
            or backlog_trend == -1
        )
        has_no_negative_conflict = att_slope > -1.0 and marks_slope > -1.0 and backlog_trend <= 0

        if has_positive_signal and has_no_negative_conflict:
            return "IMPROVING"

        # 4. Default: STABLE
        return "STABLE"

    @classmethod
    def to_risk_snapshot(cls, result: RiskFusionResult) -> RiskSnapshot:
        """
        Maps a RiskFusionResult into an ORM RiskSnapshot instance ready for append-style persistence.
        """
        return RiskSnapshot(
            student_id=result.student_id,
            computed_at=result.computed_at or datetime.now(timezone.utc),
            rule_score=result.rule_score,
            ml_probability=result.ml_probability,
            final_score=result.final_score,
            risk_tier=RiskTierEnum(result.risk_tier),
            trend=TrendEnum(result.trend),
        )
