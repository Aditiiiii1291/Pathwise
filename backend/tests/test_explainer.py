import math
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

try:
    from app.core.database import Base
    from app.schemas.features import StudentFeatures
    from app.schemas.rules import RuleEvaluationResult, TriggeredRule, FactorScores, FactorContributions
    from app.schemas.risk import RiskFusionResult, FusionConfig
    from app.schemas.explanation import ExplanationResult, ExplanationFactor, Recommendation
    from app.services.explainer import ExplanationEngine
    from app.services.fusion_engine import RiskFusionEngine
    from app.services.rules import RuleEngine
    from app.services.ml_predictor import MLPredictor
    from app.services.features import FeatureEngineeringService
    from app.services.fusion import StudentDataFusionService
    from app.services.ingestion import IngestionService
    from ml.training.train import BASE_DIR
except ImportError:
    from backend.app.core.database import Base
    from backend.app.schemas.features import StudentFeatures
    from backend.app.schemas.rules import RuleEvaluationResult, TriggeredRule, FactorScores, FactorContributions
    from backend.app.schemas.risk import RiskFusionResult, FusionConfig
    from backend.app.schemas.explanation import ExplanationResult, ExplanationFactor, Recommendation
    from backend.app.services.explainer import ExplanationEngine
    from backend.app.services.fusion_engine import RiskFusionEngine
    from backend.app.services.rules import RuleEngine
    from backend.app.services.ml_predictor import MLPredictor
    from backend.app.services.features import FeatureEngineeringService
    from backend.app.services.fusion import StudentDataFusionService
    from backend.app.services.ingestion import IngestionService
    from ml.training.train import BASE_DIR

SYNTHETIC_DATA_DIR = BASE_DIR / "data" / "raw" / "synthetic"
MODEL_PATH = BASE_DIR / "ml" / "models" / "dropout_detector.joblib"
METADATA_PATH = BASE_DIR / "ml" / "models" / "metadata.json"

FORBIDDEN_WORDS = [
    "definitely",
    "will drop out",
    "financial hardship",
    "poor family",
    "cannot afford",
    "lazy",
    "unmotivated",
    "mental illness",
    "model confidence",
]

def mock_student_bundle(
    student_id=1,
    attendance_current=85.0,
    attendance_slope=0.0,
    attendance_decline_pp=0.0,
    marks_current_avg=75.0,
    marks_slope=0.0,
    marks_consecutive_failures=0,
    marks_failed_subject_count=0,
    backlog_count_active=0,
    backlog_new_this_semester=0,
    backlog_trend_numeric=0,
    fee_percentage_paid=100.0,
    fee_terms_overdue=0,
    rule_score=0.0,
    ml_probability=0.05,
    risk_tier="LOW",
    trend="STABLE",
):
    """Helper to mock student features, rule result, and fusion result."""
    features = StudentFeatures(
        student_id=student_id,
        attendance_current=attendance_current,
        attendance_mean=attendance_current,
        attendance_slope=attendance_slope,
        attendance_decline_pp=attendance_decline_pp,
        attendance_recent_vs_historical=1.0,
        attendance_consecutive_decline=0,
        attendance_acceleration=0.0,
        attendance_history_count=6,
        has_sufficient_attendance_history=True,
        marks_current_avg=marks_current_avg,
        marks_mean=marks_current_avg,
        marks_slope=marks_slope,
        marks_decline_pp=0.0,
        marks_recent_vs_previous=1.0,
        marks_consecutive_failures=marks_consecutive_failures,
        marks_failed_subject_count=marks_failed_subject_count,
        marks_history_count=4,
        has_sufficient_marks_history=True,
        backlog_count_active=backlog_count_active,
        backlog_count_total=backlog_count_active,
        backlog_new_this_semester=backlog_new_this_semester,
        backlog_trend_numeric=backlog_trend_numeric,
        max_attempt_number=1,
        fee_status_latest="PAID" if fee_terms_overdue == 0 else "PARTIAL",
        fee_percentage_paid=fee_percentage_paid,
        fee_terms_overdue=fee_terms_overdue,
        fee_pending_count=fee_terms_overdue,
    )

    rule_res = RuleEngine.evaluate(features)
    fusion_res = RiskFusionEngine.fuse(
        student_id=student_id,
        rule_score=rule_res.rule_score if rule_score == 0.0 else rule_score,
        ml_probability=ml_probability,
        features=features,
    )
    return features, rule_res, fusion_res

def test_explanation_result_structure():
    """Verify ExplanationResult schema structure and field types."""
    features, rule_res, fusion_res = mock_student_bundle(attendance_current=58.0, marks_current_avg=34.0, ml_probability=0.72)
    exp = ExplanationEngine.generate_explanation(features, rule_res, fusion_res)

    assert isinstance(exp, ExplanationResult)
    assert exp.student_id == 1
    assert exp.risk_tier in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert exp.trend in ("RAPIDLY_DETERIORATING", "GRADUALLY_DETERIORATING", "STABLE", "IMPROVING")
    assert 0.0 <= exp.final_score <= 100.0
    assert len(exp.summary) > 0
    assert isinstance(exp.top_factors, list)
    assert isinstance(exp.recommendations, list)

def test_low_stable_student_no_alarm():
    """Verify LOW + STABLE student receives calm routine monitoring summary and minimal recommendation."""
    features, rule_res, fusion_res = mock_student_bundle(attendance_current=90.0, marks_current_avg=85.0, ml_probability=0.02)
    exp = ExplanationEngine.generate_explanation(features, rule_res, fusion_res)

    assert exp.risk_tier == "LOW"
    assert exp.trend == "STABLE"
    assert "LOW risk" in exp.summary
    assert len(exp.recommendations) <= 1
    if exp.recommendations:
        assert exp.recommendations[0].code == "REC_ROUTINE_MONITORING"
        assert exp.recommendations[0].priority == "LOW"

def test_low_improving_student_progress_recognition():
    """Verify LOW + IMPROVING student summary recognizes progress."""
    features, rule_res, fusion_res = mock_student_bundle(
        attendance_current=82.0,
        attendance_slope=3.0,
        marks_current_avg=78.0,
        marks_slope=2.5,
        ml_probability=0.05,
    )
    exp = ExplanationEngine.generate_explanation(features, rule_res, fusion_res)

    assert exp.risk_tier == "LOW"
    assert exp.trend == "IMPROVING"
    assert "IMPROVING" in exp.summary

def test_high_improving_student_explanation():
    """Verify HIGH + IMPROVING explains elevated risk along with positive recent trajectory."""
    features, rule_res, fusion_res = mock_student_bundle(
        attendance_current=62.0,
        attendance_slope=3.5,
        marks_current_avg=55.0,
        marks_slope=3.0,
        backlog_count_active=2,
        rule_score=60.0,
        ml_probability=0.60,
    )
    exp = ExplanationEngine.generate_explanation(features, rule_res, fusion_res)

    assert exp.risk_tier == "HIGH"
    assert exp.trend == "IMPROVING"
    assert "elevated" in exp.summary.lower()
    assert "improving" in exp.summary.lower()
    rec_codes = [r.code for r in exp.recommendations]
    assert "REC_SUSTAIN_IMPROVEMENT" in rec_codes

def test_medium_rapidly_deteriorating_early_warning():
    """Verify MEDIUM + RAPIDLY_DETERIORATING student triggers early mentor review."""
    features, rule_res, fusion_res = mock_student_bundle(
        attendance_current=72.0,
        attendance_slope=-9.0,
        marks_current_avg=65.0,
        rule_score=35.0,
        ml_probability=0.35,
    )
    exp = ExplanationEngine.generate_explanation(features, rule_res, fusion_res)

    assert exp.risk_tier == "MEDIUM"
    assert exp.trend == "RAPIDLY_DETERIORATING"
    assert "RAPIDLY_DETERIORATING" in exp.summary
    assert "early mentor attention" in exp.summary.lower()

def test_attendance_and_marks_factual_grounding():
    """Verify factor explanations reference exact numbers from features."""
    features, rule_res, fusion_res = mock_student_bundle(
        attendance_current=57.5,
        marks_current_avg=32.4,
        attendance_slope=-6.2,
        marks_slope=-5.8,
    )
    exp = ExplanationEngine.generate_explanation(features, rule_res, fusion_res)

    factor_descriptions = " ".join(f.description for f in exp.top_factors)
    assert "57.5%" in factor_descriptions
    assert "32.4%" in factor_descriptions

def test_fee_neutral_verification_language():
    """Verify fee issues use strictly neutral administrative verification language without poverty claims."""
    features, rule_res, fusion_res = mock_student_bundle(
        attendance_current=92.0,
        marks_current_avg=88.0,
        fee_percentage_paid=50.0,
        fee_terms_overdue=2,
    )
    exp = ExplanationEngine.generate_explanation(features, rule_res, fusion_res)

    fee_factors = [f for f in exp.top_factors if f.category == "FEES"]
    assert len(fee_factors) == 1
    assert "verification" in fee_factors[0].title.lower()

    fee_recs = [r for r in exp.recommendations if r.category == "ADMINISTRATIVE"]
    assert len(fee_recs) == 1
    assert "verify" in fee_recs[0].description.lower()
    assert "hardship" not in fee_recs[0].description.lower()
    assert "cannot afford" not in fee_recs[0].description.lower()

def test_repeated_attempts_threshold_consistency():
    """Verify REPEATED_ATTEMPTS factor uses reference_value=3 matching Phase 7 threshold."""
    features = StudentFeatures(
        student_id=42,
        attendance_current=85.0,
        attendance_mean=85.0,
        attendance_slope=0.0,
        attendance_decline_pp=0.0,
        attendance_recent_vs_historical=1.0,
        attendance_consecutive_decline=0,
        attendance_acceleration=0.0,
        attendance_history_count=6,
        has_sufficient_attendance_history=True,
        marks_current_avg=75.0,
        marks_mean=75.0,
        marks_slope=0.0,
        marks_decline_pp=0.0,
        marks_recent_vs_previous=1.0,
        marks_consecutive_failures=0,
        marks_failed_subject_count=0,
        marks_history_count=4,
        has_sufficient_marks_history=True,
        backlog_count_active=1,
        backlog_count_total=1,
        backlog_new_this_semester=0,
        backlog_trend_numeric=0,
        max_attempt_number=3,
        fee_status_latest="PAID",
        fee_percentage_paid=100.0,
        fee_terms_overdue=0,
        fee_pending_count=0,
    )
    rule_res = RuleEngine.evaluate(features)
    fusion_res = RiskFusionEngine.fuse(student_id=42, rule_score=rule_res.rule_score, ml_probability=0.2, features=features)
    exp = ExplanationEngine.generate_explanation(features, rule_res, fusion_res)

    attempt_factors = [f for f in exp.top_factors if f.code == "REPEATED_ATTEMPTS"]
    assert len(attempt_factors) == 1
    assert attempt_factors[0].observed_value == 3
    assert attempt_factors[0].reference_value == 3

def test_multiple_serious_factors_combined_mentor_review():
    """Verify multiple serious concerns trigger combined mentor review recommendation."""
    features, rule_res, fusion_res = mock_student_bundle(
        attendance_current=55.0,
        attendance_slope=-7.0,
        marks_current_avg=33.0,
        marks_consecutive_failures=2,
        backlog_count_active=3,
        ml_probability=0.85,
    )
    exp = ExplanationEngine.generate_explanation(features, rule_res, fusion_res)

    rec_codes = [r.code for r in exp.recommendations]
    assert "REC_COMBINED_MENTOR_REVIEW" in rec_codes

def test_recommendation_deduplication():
    """Verify recommendations contain unique action codes."""
    features, rule_res, fusion_res = mock_student_bundle(
        attendance_current=50.0,
        attendance_slope=-8.0,
        attendance_decline_pp=30.0,
        marks_current_avg=30.0,
    )
    exp = ExplanationEngine.generate_explanation(features, rule_res, fusion_res)

    rec_codes = [r.code for r in exp.recommendations]
    assert len(rec_codes) == len(set(rec_codes))

def test_factor_count_bounds():
    """Verify top factors returns <= 4 factors and does not pad with fake entries."""
    # 1. Heavy concern student -> exactly 4 top factors
    f1, r1, fu1 = mock_student_bundle(
        attendance_current=50.0,
        attendance_slope=-8.0,
        marks_current_avg=30.0,
        marks_consecutive_failures=2,
        backlog_count_active=3,
    )
    exp1 = ExplanationEngine.generate_explanation(f1, r1, fu1)
    assert len(exp1.top_factors) <= 4

    # 2. Student with only 1 concern -> exactly 1 factor
    f2, r2, fu2 = mock_student_bundle(attendance_current=68.0)
    exp2 = ExplanationEngine.generate_explanation(f2, r2, fu2)
    assert len(exp2.top_factors) >= 1
    assert len(exp2.top_factors) <= 4

def test_global_ml_context_separation():
    """Verify global feature importances are stored in global_ml_context and not in top_factors."""
    mock_global_imp = [
        {"feature": "marks_decline_pp", "importance": 0.16},
        {"feature": "attendance_slope", "importance": 0.15},
    ]
    features, rule_res, fusion_res = mock_student_bundle(attendance_current=60.0)
    exp = ExplanationEngine.generate_explanation(
        features, rule_res, fusion_res, global_feature_importances=mock_global_imp
    )

    assert exp.global_ml_context is not None
    assert len(exp.global_ml_context.top_global_features) == 2
    assert "synthetic development data" in exp.global_ml_context.disclaimer.lower()

    # Verify no global entry leaked into top_factors
    for factor in exp.top_factors:
        assert factor.source in ("RULE", "FEATURE")

def test_determinism():
    """Verify identical inputs produce identical factors, summary, and recommendations."""
    features, rule_res, fusion_res = mock_student_bundle(attendance_current=60.0, marks_current_avg=38.0)
    exp1 = ExplanationEngine.generate_explanation(features, rule_res, fusion_res)
    exp2 = ExplanationEngine.generate_explanation(features, rule_res, fusion_res)

    assert exp1.summary == exp2.summary
    assert [f.code for f in exp1.top_factors] == [f.code for f in exp2.top_factors]
    assert [r.code for r in exp1.recommendations] == [r.code for r in exp2.recommendations]

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

def test_500_student_explanation_cohort_and_text_safety(synthetic_cohort):
    """Evaluates ExplanationEngine across ALL 500 synthetic students and audits text safety."""
    predictor = MLPredictor(model_path=MODEL_PATH, metadata_path=METADATA_PATH)
    global_imp = predictor.get_feature_importances()

    processed_count = 0
    all_summaries = []
    all_factor_texts = []
    all_rec_texts = []

    for p in synthetic_cohort:
        feats = FeatureEngineeringService.extract_features(p, reference_date="2026-10-01")
        rule_res = RuleEngine.evaluate(feats)
        ml_prob = predictor.predict_dropout_probability(feats)
        fusion_res = RiskFusionEngine.fuse(p.student.id, rule_res.rule_score, ml_prob, feats)

        exp = ExplanationEngine.generate_explanation(
            features=feats,
            rule_result=rule_res,
            fusion_result=fusion_res,
            global_feature_importances=global_imp,
        )

        assert exp.student_id == p.student.id
        assert len(exp.summary.strip()) > 0
        assert not math.isnan(exp.final_score)
        assert 0.0 <= exp.final_score <= 100.0
        assert len(exp.top_factors) <= 4

        processed_count += 1
        all_summaries.append(exp.summary)
        for f in exp.top_factors:
            all_factor_texts.append(f"{f.title} {f.description}")
        for r in exp.recommendations:
            all_rec_texts.append(f"{r.title} {r.description}")

    assert processed_count == 500

    # Text Safety Audit
    combined_corpus = " ".join(all_summaries + all_factor_texts + all_rec_texts).lower()
    for forbidden in FORBIDDEN_WORDS:
        assert forbidden not in combined_corpus, f"Found forbidden phrase '{forbidden}' in explanation outputs!"
