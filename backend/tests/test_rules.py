import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

try:
    from app.core.database import Base
    from app.schemas.features import StudentFeatures
    from app.schemas.rules import (
        RuleEngineConfig,
        RuleWeights,
        RuleThresholds,
        RuleEvaluationResult,
    )
    from app.services.rules import RuleEngine
    from app.services.features import FeatureEngineeringService
    from app.services.fusion import StudentDataFusionService
    from app.services.ingestion import IngestionService
    from ml.data_generation.generator import SyntheticDataGenerator
except ImportError:
    from backend.app.core.database import Base
    from backend.app.schemas.features import StudentFeatures
    from backend.app.schemas.rules import (
        RuleEngineConfig,
        RuleWeights,
        RuleThresholds,
        RuleEvaluationResult,
    )
    from backend.app.services.rules import RuleEngine
    from backend.app.services.features import FeatureEngineeringService
    from backend.app.services.fusion import StudentDataFusionService
    from backend.app.services.ingestion import IngestionService
    from ml.data_generation.generator import SyntheticDataGenerator

def mock_features(
    student_id=101,
    attendance_current=85.0,
    attendance_slope=0.0,
    attendance_decline_pp=0.0,
    attendance_consecutive_decline=0,
    attendance_acceleration=0.0,
    has_sufficient_attendance_history=True,
    marks_current_avg=75.0,
    marks_slope=0.0,
    marks_decline_pp=0.0,
    marks_consecutive_failures=0,
    marks_failed_subject_count=0,
    has_sufficient_marks_history=True,
    backlog_count_active=0,
    backlog_new_this_semester=0,
    backlog_trend_numeric=0,
    max_attempt_number=1,
    fee_status_latest="PAID",
    fee_percentage_paid=100.0,
    fee_terms_overdue=0,
    fee_pending_count=0,
):
    """Helper to build a custom StudentFeatures object."""
    return StudentFeatures(
        student_id=student_id,
        attendance_current=attendance_current,
        attendance_mean=attendance_current,
        attendance_slope=attendance_slope,
        attendance_decline_pp=attendance_decline_pp,
        attendance_recent_vs_historical=1.0,
        attendance_consecutive_decline=attendance_consecutive_decline,
        attendance_acceleration=attendance_acceleration,
        attendance_history_count=5 if has_sufficient_attendance_history else 1,
        has_sufficient_attendance_history=has_sufficient_attendance_history,
        marks_current_avg=marks_current_avg,
        marks_mean=marks_current_avg,
        marks_slope=marks_slope,
        marks_decline_pp=marks_decline_pp,
        marks_recent_vs_previous=1.0,
        marks_consecutive_failures=marks_consecutive_failures,
        marks_failed_subject_count=marks_failed_subject_count,
        marks_history_count=4 if has_sufficient_marks_history else 1,
        has_sufficient_marks_history=has_sufficient_marks_history,
        backlog_count_active=backlog_count_active,
        backlog_count_total=backlog_count_active,
        backlog_new_this_semester=backlog_new_this_semester,
        backlog_trend_numeric=backlog_trend_numeric,
        max_attempt_number=max_attempt_number,
        fee_status_latest=fee_status_latest,
        fee_percentage_paid=fee_percentage_paid,
        fee_terms_overdue=fee_terms_overdue,
        fee_pending_count=fee_pending_count,
    )

def test_default_config_validates():
    """Verify default rule configuration creates valid weights summing to 1.0."""
    config = RuleEngineConfig()
    assert config.weights.attendance == 0.30
    assert config.weights.marks == 0.25
    assert config.weights.backlogs == 0.15
    assert config.weights.fees == 0.10
    assert config.weights.trends == 0.20
    assert abs(config.weights.attendance + config.weights.marks + config.weights.backlogs + config.weights.fees + config.weights.trends - 1.0) < 1e-4

def test_invalid_weight_sum_rejected():
    """Verify weights not summing to 1.0 are rejected."""
    with pytest.raises(ValidationError):
        RuleWeights(attendance=0.5, marks=0.5, backlogs=0.5, fees=0.1, trends=0.2)

def test_negative_weight_rejected():
    """Verify negative weights are rejected."""
    with pytest.raises(ValidationError):
        RuleWeights(attendance=-0.1, marks=0.4, backlogs=0.2, fees=0.2, trends=0.3)

def test_healthy_student_low_score_and_no_triggers():
    """Verify healthy student produces low rule score and no critical triggers."""
    feats = mock_features()
    result = RuleEngine.evaluate(feats)

    assert result.rule_score == 0.0
    assert len(result.triggered_rules) == 0
    assert result.factor_scores.attendance == 0.0
    assert result.factor_scores.marks == 0.0

def test_attendance_below_threshold_trigger():
    """Verify low attendance triggers ATTENDANCE_BELOW_THRESHOLD."""
    feats = mock_features(attendance_current=55.0)
    result = RuleEngine.evaluate(feats)

    assert result.factor_scores.attendance > 0.0
    codes = [r.code for r in result.triggered_rules]
    assert "ATTENDANCE_BELOW_THRESHOLD" in codes

def test_attendance_decline_triggers():
    """Verify negative slope and large decline trigger corresponding rules."""
    feats = mock_features(attendance_current=60.0, attendance_slope=-8.0, attendance_decline_pp=25.0)
    result = RuleEngine.evaluate(feats)

    codes = [r.code for r in result.triggered_rules]
    assert "ATTENDANCE_DECLINING" in codes
    assert "ATTENDANCE_LARGE_DECLINE" in codes

def test_insufficient_attendance_history_skips_trend_rules():
    """Verify sparse attendance (1 record) does NOT trigger slope/trend rules."""
    feats = mock_features(
        attendance_current=60.0,
        attendance_slope=-10.0,
        has_sufficient_attendance_history=False
    )
    result = RuleEngine.evaluate(feats)

    codes = [r.code for r in result.triggered_rules]
    assert "ATTENDANCE_BELOW_THRESHOLD" in codes
    assert "ATTENDANCE_DECLINING" not in codes

def test_marks_rules_triggers():
    """Verify marks triggers for low score, consecutive failures, and failing subjects."""
    feats = mock_features(
        marks_current_avg=32.0,
        marks_consecutive_failures=2,
        marks_failed_subject_count=2,
        marks_slope=-7.0,
    )
    result = RuleEngine.evaluate(feats)

    codes = [r.code for r in result.triggered_rules]
    assert "MARKS_BELOW_THRESHOLD" in codes
    assert "REPEATED_FAILURES" in codes
    assert "MULTIPLE_FAILED_SUBJECTS" in codes
    assert "MARKS_DECLINING" in codes

def test_backlog_rules_and_temporal_trend():
    """Verify backlog rules including active count, semester additions, and temporal trend."""
    feats = mock_features(
        backlog_count_active=3,
        backlog_new_this_semester=1,
        backlog_trend_numeric=1,
        max_attempt_number=3,
    )
    result = RuleEngine.evaluate(feats)

    codes = [r.code for r in result.triggered_rules]
    assert "MULTIPLE_ACTIVE_BACKLOGS" in codes
    assert "NEW_BACKLOGS_CURRENT_SEMESTER" in codes
    assert "BACKLOGS_INCREASING" in codes
    assert "REPEATED_ATTEMPTS" in codes

def test_decreasing_backlog_does_not_trigger_increasing():
    """Verify decreasing backlog trend (-1) does not trigger BACKLOGS_INCREASING."""
    feats = mock_features(backlog_count_active=1, backlog_trend_numeric=-1)
    result = RuleEngine.evaluate(feats)

    codes = [r.code for r in result.triggered_rules]
    assert "BACKLOGS_INCREASING" not in codes

def test_fee_context_trigger_and_fairness():
    """Verify fee overdue triggers verification rule, but cannot dominate overall score."""
    feats = mock_features(
        attendance_current=92.0,
        marks_current_avg=88.0,
        backlog_count_active=0,
        fee_status_latest="PARTIAL",
        fee_percentage_paid=40.0,
        fee_terms_overdue=2,
        fee_pending_count=1,
    )
    result = RuleEngine.evaluate(feats)

    codes = [r.code for r in result.triggered_rules]
    assert "FEE_VERIFICATION_RECOMMENDED" in codes

    # Fee score exists, but because fee weight is 0.10, rule_score is strictly capped
    assert result.factor_contributions.fees <= 10.0
    assert result.rule_score <= 15.0

def test_factor_contributions_sum_to_rule_score():
    """Verify sum of factor contributions matches final rule score within precision."""
    feats = mock_features(
        attendance_current=62.0,
        attendance_slope=-6.0,
        marks_current_avg=45.0,
        backlog_count_active=2,
        fee_status_latest="PARTIAL",
        fee_terms_overdue=1,
    )
    result = RuleEngine.evaluate(feats)

    contrib_sum = (
        result.factor_contributions.attendance
        + result.factor_contributions.marks
        + result.factor_contributions.backlogs
        + result.factor_contributions.fees
        + result.factor_contributions.trends
    )
    assert abs(contrib_sum - result.rule_score) < 0.05
    assert 0.0 <= result.rule_score <= 100.0

def test_determinism():
    """Verify identical features and config produce exactly identical output."""
    feats = mock_features(attendance_current=65.0, marks_current_avg=42.0)
    res1 = RuleEngine.evaluate(feats)
    res2 = RuleEngine.evaluate(feats)

    assert res1.rule_score == res2.rule_score
    assert len(res1.triggered_rules) == len(res2.triggered_rules)

def test_explanations_are_factual_and_non_stigmatizing():
    """Verify generated explanations avoid dropout predictions or stigmatizing language."""
    feats = mock_features(
        attendance_current=55.0,
        marks_current_avg=35.0,
        fee_status_latest="PENDING",
        fee_terms_overdue=1
    )
    result = RuleEngine.evaluate(feats)

    for rule in result.triggered_rules:
        msg = rule.message.lower()
        assert "drop out" not in msg
        assert "dropout" not in msg
        assert "irresponsible" not in msg
        assert "cannot afford" not in msg
        assert "distress" not in msg

def test_end_to_end_pipeline_integration():
    """Integration: Ingest via Phase 4 -> Fuse via Phase 5 -> Features via Phase 6 -> Rules via Phase 7."""
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()

    try:
        ingestion = IngestionService(session)

        # 1. Ingest Student
        student_csv = "student_id,roll_number,name,department,semester\n801,CS801,Margaret Hamilton,CSE,4\n"
        ingestion.ingest("students", "students.csv", student_csv.encode("utf-8"))

        # 2. Ingest Attendance: [90, 80, 70, 60] (Deteriorating)
        att_csv = (
            "student_id,week_number,month,total_classes,attended_classes\n"
            "801,1,August,20,18\n"
            "801,2,August,20,16\n"
            "801,3,August,20,14\n"
            "801,4,August,20,12\n"
        )
        ingestion.ingest("attendance", "att.csv", att_csv.encode("utf-8"))

        # 3. Ingest Marks (Failing)
        marks_csv = "student_id,subject_name,exam_type,max_marks,obtained_marks\n801,Math,FINAL,100,35\n"
        ingestion.ingest("marks", "marks.csv", marks_csv.encode("utf-8"))

        # 4. Fuse
        fusion = StudentDataFusionService(session)
        profile = fusion.fuse_by_id(801)
        assert profile is not None

        # 5. Extract Features
        feats = FeatureEngineeringService.extract_features(profile)

        # 6. Evaluate Rules
        eval_result = RuleEngine.evaluate(feats)
        assert eval_result.student_id == 801
        assert eval_result.rule_score > 20.0
        codes = [r.code for r in eval_result.triggered_rules]
        assert "ATTENDANCE_BELOW_THRESHOLD" in codes
        assert "MARKS_BELOW_THRESHOLD" in codes

    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

def test_cohort_sanity_check(tmp_path):
    """Sanity check: evaluate rule engine over synthetic cohort ensuring 0 errors/NaNs and bounds [0, 100]."""
    temp_dir = str(tmp_path / "cohort_rules")
    gen = SyntheticDataGenerator(num_students=50, seed=42, output_dir=temp_dir)
    gen.generate().save()

    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()

    try:
        ingestion = IngestionService(session)
        with open(f"{temp_dir}/students_roster.csv", "rb") as f:
            ingestion.ingest("students", "students.csv", f.read())
        with open(f"{temp_dir}/attendance.csv", "rb") as f:
            ingestion.ingest("attendance", "att.csv", f.read())
        with open(f"{temp_dir}/marks.csv", "rb") as f:
            ingestion.ingest("marks", "marks.csv", f.read())
        with open(f"{temp_dir}/fees.csv", "rb") as f:
            ingestion.ingest("fees", "fees.csv", f.read())
        with open(f"{temp_dir}/attempts.csv", "rb") as f:
            ingestion.ingest("attempts", "attempts.csv", f.read())

        fusion = StudentDataFusionService(session)
        profiles = fusion.fuse_all(limit=50)

        scores = []
        for p in profiles:
            feats = FeatureEngineeringService.extract_features(p)
            res = RuleEngine.evaluate(feats)
            assert 0.0 <= res.rule_score <= 100.0
            scores.append(res.rule_score)

        assert len(scores) == 50
        assert max(scores) > min(scores)

    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
