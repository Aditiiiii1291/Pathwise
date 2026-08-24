import math
import pytest
from datetime import datetime
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

try:
    from app.core.database import Base
    from app.schemas.features import StudentFeatures
    from app.schemas.risk import FusionConfig, RiskFusionResult
    from app.services.fusion_engine import RiskFusionEngine
    from app.services.rules import RuleEngine
    from app.services.ml_predictor import MLPredictor
    from app.services.features import FeatureEngineeringService
    from app.services.fusion import StudentDataFusionService
    from app.services.ingestion import IngestionService
    from app.models.risk import RiskSnapshot, RiskTierEnum, TrendEnum
    from ml.training.train import BASE_DIR
except ImportError:
    from backend.app.core.database import Base
    from backend.app.schemas.features import StudentFeatures
    from backend.app.schemas.risk import FusionConfig, RiskFusionResult
    from backend.app.services.fusion_engine import RiskFusionEngine
    from backend.app.services.rules import RuleEngine
    from backend.app.services.ml_predictor import MLPredictor
    from backend.app.services.features import FeatureEngineeringService
    from backend.app.services.fusion import StudentDataFusionService
    from backend.app.services.ingestion import IngestionService
    from backend.app.models.risk import RiskSnapshot, RiskTierEnum, TrendEnum
    from ml.training.train import BASE_DIR

SYNTHETIC_DATA_DIR = BASE_DIR / "data" / "raw" / "synthetic"
MODEL_PATH = BASE_DIR / "ml" / "models" / "dropout_detector.joblib"
METADATA_PATH = BASE_DIR / "ml" / "models" / "metadata.json"

def mock_features(
    student_id=1,
    attendance_slope=0.0,
    attendance_acceleration=0.0,
    attendance_consecutive_decline=0,
    attendance_decline_pp=0.0,
    has_sufficient_attendance_history=True,
    marks_slope=0.0,
    marks_consecutive_failures=0,
    marks_decline_pp=0.0,
    has_sufficient_marks_history=True,
    backlog_trend_numeric=0,
):
    """Helper to mock student features for trend testing."""
    return StudentFeatures(
        student_id=student_id,
        attendance_current=80.0,
        attendance_mean=80.0,
        attendance_slope=attendance_slope,
        attendance_decline_pp=attendance_decline_pp,
        attendance_recent_vs_historical=1.0,
        attendance_consecutive_decline=attendance_consecutive_decline,
        attendance_acceleration=attendance_acceleration,
        attendance_history_count=6 if has_sufficient_attendance_history else 1,
        has_sufficient_attendance_history=has_sufficient_attendance_history,
        marks_current_avg=70.0,
        marks_mean=70.0,
        marks_slope=marks_slope,
        marks_decline_pp=marks_decline_pp,
        marks_recent_vs_previous=1.0,
        marks_consecutive_failures=marks_consecutive_failures,
        marks_failed_subject_count=0,
        marks_history_count=4 if has_sufficient_marks_history else 1,
        has_sufficient_marks_history=has_sufficient_marks_history,
        backlog_count_active=0,
        backlog_count_total=0,
        backlog_new_this_semester=0,
        backlog_trend_numeric=backlog_trend_numeric,
        max_attempt_number=1,
        fee_status_latest="PAID",
        fee_percentage_paid=100.0,
        fee_terms_overdue=0,
        fee_pending_count=0,
    )

def test_default_fusion_config():
    """Verify default FusionConfig is 0.5 / 0.5."""
    cfg = FusionConfig()
    assert cfg.rule_weight == 0.5
    assert cfg.ml_weight == 0.5

def test_custom_valid_weights():
    """Verify custom valid weight combinations are accepted."""
    cfg1 = FusionConfig(rule_weight=0.6, ml_weight=0.4)
    assert cfg1.rule_weight == 0.6
    assert cfg1.ml_weight == 0.4

    cfg2 = FusionConfig(rule_weight=0.4, ml_weight=0.6)
    assert cfg2.rule_weight == 0.4
    assert cfg2.ml_weight == 0.6

def test_invalid_weights_rejected():
    """Verify invalid weights are rejected with ValidationError."""
    with pytest.raises(ValidationError):
        FusionConfig(rule_weight=0.8, ml_weight=0.8)
    with pytest.raises(ValidationError):
        FusionConfig(rule_weight=-0.1, ml_weight=1.1)
    with pytest.raises(ValidationError):
        FusionConfig(rule_weight=1.2, ml_weight=-0.2)

def test_invalid_inputs_rejected():
    """Verify out-of-range rule_score and ml_probability raise ValueError."""
    feats = mock_features()
    with pytest.raises(ValueError):
        RiskFusionEngine.fuse(student_id=1, rule_score=-5.0, ml_probability=0.5, features=feats)
    with pytest.raises(ValueError):
        RiskFusionEngine.fuse(student_id=1, rule_score=105.0, ml_probability=0.5, features=feats)
    with pytest.raises(ValueError):
        RiskFusionEngine.fuse(student_id=1, rule_score=50.0, ml_probability=-0.1, features=feats)
    with pytest.raises(ValueError):
        RiskFusionEngine.fuse(student_id=1, rule_score=50.0, ml_probability=1.2, features=feats)

def test_weighted_fusion_calculations():
    """Verify 50/50, 60/40, and 40/60 fusion calculations."""
    feats = mock_features()

    # 50/50: 60 * 0.5 + 0.8 * 100 * 0.5 = 30 + 40 = 70.0
    res_50 = RiskFusionEngine.fuse(student_id=1, rule_score=60.0, ml_probability=0.8, features=feats)
    assert res_50.final_score == 70.0
    assert res_50.risk_tier == "HIGH"

    # 60/40: 60 * 0.6 + 80 * 0.4 = 36 + 32 = 68.0
    res_60 = RiskFusionEngine.fuse(student_id=1, rule_score=60.0, ml_probability=0.8, features=feats, config=FusionConfig(rule_weight=0.6, ml_weight=0.4))
    assert res_60.final_score == 68.0

    # 40/60: 60 * 0.4 + 80 * 0.6 = 24 + 48 = 72.0
    res_40 = RiskFusionEngine.fuse(student_id=1, rule_score=60.0, ml_probability=0.8, features=feats, config=FusionConfig(rule_weight=0.4, ml_weight=0.6))
    assert res_40.final_score == 72.0

def test_continuous_risk_tier_boundaries():
    """Verify exact continuous risk tier boundaries."""
    feats = mock_features()

    # LOW: [0, 25)
    assert RiskFusionEngine.fuse(1, 0.0, 0.0, feats).risk_tier == "LOW"
    assert RiskFusionEngine.fuse(1, 24.99, 0.2499, feats).risk_tier == "LOW"

    # MEDIUM: [25, 50)
    assert RiskFusionEngine.fuse(1, 25.0, 0.25, feats).risk_tier == "MEDIUM"
    assert RiskFusionEngine.fuse(1, 49.99, 0.4999, feats).risk_tier == "MEDIUM"

    # HIGH: [50, 75)
    assert RiskFusionEngine.fuse(1, 50.0, 0.50, feats).risk_tier == "HIGH"
    assert RiskFusionEngine.fuse(1, 74.99, 0.7499, feats).risk_tier == "HIGH"

    # CRITICAL: [75, 100]
    assert RiskFusionEngine.fuse(1, 75.0, 0.75, feats).risk_tier == "CRITICAL"
    assert RiskFusionEngine.fuse(1, 100.0, 1.0, feats).risk_tier == "CRITICAL"

def test_raw_score_used_before_rounding():
    """Verify 49.999 raw score is MEDIUM and not rounded up to HIGH before tier assignment."""
    feats = mock_features()
    # 49.998 rule + 0.5 ml -> 49.999
    res = RiskFusionEngine.fuse(student_id=1, rule_score=49.998, ml_probability=0.5, features=feats)
    assert res.risk_tier == "MEDIUM"

def test_trend_classifications():
    """Verify temporal trend classification across all 4 categories."""
    # 1. RAPIDLY_DETERIORATING
    rapid_feats = mock_features(attendance_slope=-8.5)
    assert RiskFusionEngine.fuse(1, 50.0, 0.5, rapid_feats).trend == "RAPIDLY_DETERIORATING"

    # 2. GRADUALLY_DETERIORATING
    gradual_feats = mock_features(attendance_slope=-2.5)
    assert RiskFusionEngine.fuse(1, 50.0, 0.5, gradual_feats).trend == "GRADUALLY_DETERIORATING"

    # 3. IMPROVING
    improving_feats = mock_features(attendance_slope=3.0, marks_slope=2.5)
    assert RiskFusionEngine.fuse(1, 50.0, 0.5, improving_feats).trend == "IMPROVING"

    # 4. STABLE
    stable_feats = mock_features(attendance_slope=0.2, marks_slope=-0.1)
    assert RiskFusionEngine.fuse(1, 50.0, 0.5, stable_feats).trend == "STABLE"

def test_conflicting_trend_signals():
    """Verify deterioration takes precedence over mild improvement when signals conflict."""
    conflicting_feats = mock_features(attendance_slope=2.0, marks_slope=-7.0)
    res = RiskFusionEngine.fuse(1, 50.0, 0.5, conflicting_feats)
    assert res.trend in ("RAPIDLY_DETERIORATING", "GRADUALLY_DETERIORATING")

def test_risk_tier_independent_from_trend():
    """Verify HIGH risk + IMPROVING and MEDIUM risk + RAPIDLY_DETERIORATING can both exist."""
    # High risk but improving
    improving_high = mock_features(attendance_slope=3.0, marks_slope=2.5)
    res1 = RiskFusionEngine.fuse(1, 60.0, 0.6, improving_high)
    assert res1.risk_tier == "HIGH"
    assert res1.trend == "IMPROVING"

    # Medium risk but rapidly deteriorating
    rapid_med = mock_features(attendance_slope=-9.0)
    res2 = RiskFusionEngine.fuse(1, 30.0, 0.3, rapid_med)
    assert res2.risk_tier == "MEDIUM"
    assert res2.trend == "RAPIDLY_DETERIORATING"

def test_disagreement_cases():
    """Verify fusion behavior on high/low rule vs ML disagreement."""
    feats = mock_features()

    # Case A: Rule 80, ML 0.20 -> 50.0 -> HIGH
    resA = RiskFusionEngine.fuse(1, 80.0, 0.20, feats)
    assert resA.final_score == 50.0
    assert resA.risk_tier == "HIGH"

    # Case B: Rule 20, ML 0.80 -> 50.0 -> HIGH
    resB = RiskFusionEngine.fuse(1, 20.0, 0.80, feats)
    assert resB.final_score == 50.0
    assert resB.risk_tier == "HIGH"

    # Case C: Rule 10, ML 0.10 -> 10.0 -> LOW
    resC = RiskFusionEngine.fuse(1, 10.0, 0.10, feats)
    assert resC.final_score == 10.0
    assert resC.risk_tier == "LOW"

    # Case D: Rule 90, ML 0.90 -> 90.0 -> CRITICAL
    resD = RiskFusionEngine.fuse(1, 90.0, 0.90, feats)
    assert resD.final_score == 90.0
    assert resD.risk_tier == "CRITICAL"

def test_determinism_and_field_preservation():
    """Verify result preserves component values and is completely deterministic."""
    feats = mock_features()
    res1 = RiskFusionEngine.fuse(101, 65.0, 0.72, feats)
    res2 = RiskFusionEngine.fuse(101, 65.0, 0.72, feats)

    assert res1.student_id == 101
    assert res1.rule_score == 65.0
    assert res1.ml_probability == 0.72
    assert res1.ml_score == 72.0
    assert res1.rule_weight == 0.5
    assert res1.ml_weight == 0.5
    assert res1.final_score == 68.5
    assert res1.risk_tier == "HIGH"
    assert res1.final_score == res2.final_score
    assert res1.risk_tier == res2.risk_tier

def test_risk_snapshot_compatibility():
    """Verify RiskFusionResult maps cleanly to ORM RiskSnapshot model."""
    feats = mock_features()
    res = RiskFusionEngine.fuse(101, 55.0, 0.60, feats)
    snapshot = RiskFusionEngine.to_risk_snapshot(res)

    assert isinstance(snapshot, RiskSnapshot)
    assert snapshot.student_id == 101
    assert snapshot.rule_score == 55.0
    assert snapshot.ml_probability == 0.60
    assert snapshot.final_score == 57.5
    assert snapshot.risk_tier == RiskTierEnum.HIGH
    assert snapshot.trend in TrendEnum

@pytest.fixture(scope="module")
def synthetic_cohort():
    """Loads and fuses full 500 synthetic cohort into memory."""
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()

    try:
        ingestion = IngestionService(session)
        with open(SYNTHETIC_DATA_DIR / "students_roster.csv", "rb") as f:
            ingestion.ingest("students", "students.csv", f.read())
        with open(SYNTHETIC_DATA_DIR / "attendance.csv", "rb") as f:
            ingestion.ingest("attendance", "att.csv", f.read())
        with open(SYNTHETIC_DATA_DIR / "marks.csv", "rb") as f:
            ingestion.ingest("marks", "marks.csv", f.read())
        with open(SYNTHETIC_DATA_DIR / "fees.csv", "rb") as f:
            ingestion.ingest("fees", "fees.csv", f.read())
        with open(SYNTHETIC_DATA_DIR / "attempts.csv", "rb") as f:
            ingestion.ingest("attempts", "attempts.csv", f.read())

        fusion = StudentDataFusionService(session)
        profiles = fusion.fuse_all(limit=500)
        yield profiles
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

def test_500_student_risk_fusion_cohort(synthetic_cohort):
    """Evaluates full 500 synthetic cohort through Phase 6 -> 7 & 8 -> 9 Risk Fusion."""
    predictor = MLPredictor(model_path=MODEL_PATH, metadata_path=METADATA_PATH)

    results_50 = []
    results_60 = []
    results_40 = []

    diffs = []
    tier_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    trend_counts = {"IMPROVING": 0, "STABLE": 0, "GRADUALLY_DETERIORATING": 0, "RAPIDLY_DETERIORATING": 0}

    for p in synthetic_cohort:
        feats = FeatureEngineeringService.extract_features(p, reference_date="2026-10-01")
        rule_res = RuleEngine.evaluate(feats)
        ml_prob = predictor.predict_dropout_probability(feats)

        # 50/50 Default
        res50 = RiskFusionEngine.fuse(p.student.id, rule_res.rule_score, ml_prob, feats)
        assert not math.isnan(res50.final_score)
        assert not math.isinf(res50.final_score)
        assert 0.0 <= res50.final_score <= 100.0
        results_50.append(res50)
        tier_counts[res50.risk_tier] += 1
        trend_counts[res50.trend] += 1

        # Disagreement
        diff = abs(rule_res.rule_score - (ml_prob * 100.0))
        diffs.append(diff)

        # 60/40 Sensitivity
        res60 = RiskFusionEngine.fuse(p.student.id, rule_res.rule_score, ml_prob, feats, config=FusionConfig(rule_weight=0.6, ml_weight=0.4))
        results_60.append(res60)

        # 40/60 Sensitivity
        res40 = RiskFusionEngine.fuse(p.student.id, rule_res.rule_score, ml_prob, feats, config=FusionConfig(rule_weight=0.4, ml_weight=0.6))
        results_40.append(res40)

    assert len(results_50) == 500
    assert sum(tier_counts.values()) == 500
    assert sum(trend_counts.values()) == 500
    assert min(r.final_score for r in results_50) >= 0.0
    assert max(r.final_score for r in results_50) <= 100.0
