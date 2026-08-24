import math
import pytest
from pathlib import Path
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

try:
    from app.core.database import Base
    from app.schemas.features import StudentFeatures
    from app.services.features import FeatureEngineeringService
    from app.services.fusion import StudentDataFusionService
    from app.services.ingestion import IngestionService
    from app.services.rules import RuleEngine
    from app.services.ml_predictor import MLPredictor
    from ml.training.train import (
        ML_FEATURE_NAMES,
        load_training_dataset,
        train_model,
        BASE_DIR,
    )
except ImportError:
    from backend.app.core.database import Base
    from backend.app.schemas.features import StudentFeatures
    from backend.app.services.features import FeatureEngineeringService
    from backend.app.services.fusion import StudentDataFusionService
    from backend.app.services.ingestion import IngestionService
    from backend.app.services.rules import RuleEngine
    from backend.app.services.ml_predictor import MLPredictor
    from ml.training.train import (
        ML_FEATURE_NAMES,
        load_training_dataset,
        train_model,
        BASE_DIR,
    )

SYNTHETIC_DATA_DIR = BASE_DIR / "data" / "raw" / "synthetic"
MODEL_PATH = BASE_DIR / "ml" / "models" / "dropout_detector.joblib"
METADATA_PATH = BASE_DIR / "ml" / "models" / "metadata.json"

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

def test_step0_phase7_full_500_cohort_check(synthetic_cohort):
    """Step 0: Evaluate Phase 7 rule engine across ALL 500 synthetic students."""
    assert len(synthetic_cohort) == 500

    scores = []
    for p in synthetic_cohort:
        feats = FeatureEngineeringService.extract_features(p, reference_date="2026-10-01")
        result = RuleEngine.evaluate(feats)
        assert not math.isnan(result.rule_score)
        assert not math.isinf(result.rule_score)
        assert 0.0 <= result.rule_score <= 100.0
        scores.append(result.rule_score)

    assert len(scores) == 500
    assert min(scores) >= 0.0
    assert max(scores) <= 100.0
    assert max(scores) > min(scores)

def test_training_dataset_leakage_exclusion():
    """Verify X matrix excludes all target, trajectory, and personal identity fields."""
    X, y, trajectories = load_training_dataset(SYNTHETIC_DATA_DIR)

    assert len(X) == 500
    assert len(y) == 500
    assert len(X.columns) == len(ML_FEATURE_NAMES)

    # Critical leakage checks
    excluded_fields = [
        "dropout_label",
        "trajectory_type",
        "student_id",
        "roll_number",
        "name",
        "department",
        "guardian_name",
        "guardian_phone",
        "guardian_email",
        "mentor_id",
        "rule_score",
        "factor_scores",
        "triggered_rules",
    ]
    for field in excluded_fields:
        assert field not in X.columns

def test_ml_predictor_inference():
    """Verify ML inference service returns valid probability between 0.0 and 1.0."""
    predictor = MLPredictor(model_path=MODEL_PATH, metadata_path=METADATA_PATH)

    # Mock features
    mock_feats = StudentFeatures(
        student_id=999,
        attendance_current=60.0,
        attendance_mean=70.0,
        attendance_slope=-8.0,
        attendance_decline_pp=25.0,
        attendance_recent_vs_historical=0.8,
        attendance_consecutive_decline=3,
        attendance_acceleration=-1.2,
        attendance_history_count=8,
        has_sufficient_attendance_history=True,
        marks_current_avg=38.0,
        marks_mean=45.0,
        marks_slope=-6.0,
        marks_decline_pp=20.0,
        marks_recent_vs_previous=0.75,
        marks_consecutive_failures=2,
        marks_failed_subject_count=2,
        marks_history_count=4,
        has_sufficient_marks_history=True,
        backlog_count_active=2,
        backlog_count_total=3,
        backlog_new_this_semester=1,
        backlog_trend_numeric=1,
        max_attempt_number=2,
        fee_status_latest="PAID",
        fee_percentage_paid=100.0,
        fee_terms_overdue=0,
        fee_pending_count=0,
    )

    prob = predictor.predict_dropout_probability(mock_feats)
    assert 0.0 <= prob <= 1.0
    assert isinstance(prob, float)

def test_ml_predictor_determinism_and_feature_order_safety():
    """Verify prediction is deterministic and resilient to input field ordering."""
    predictor = MLPredictor(model_path=MODEL_PATH, metadata_path=METADATA_PATH)

    feats1 = StudentFeatures(
        student_id=1,
        attendance_current=85.0,
        attendance_mean=88.0,
        attendance_slope=0.0,
        attendance_decline_pp=0.0,
        attendance_recent_vs_historical=1.0,
        attendance_consecutive_decline=0,
        attendance_acceleration=0.0,
        attendance_history_count=8,
        has_sufficient_attendance_history=True,
        marks_current_avg=78.0,
        marks_mean=80.0,
        marks_slope=0.0,
        marks_decline_pp=0.0,
        marks_recent_vs_previous=1.0,
        marks_consecutive_failures=0,
        marks_failed_subject_count=0,
        marks_history_count=4,
        has_sufficient_marks_history=True,
        backlog_count_active=0,
        backlog_count_total=0,
        backlog_new_this_semester=0,
        backlog_trend_numeric=0,
        max_attempt_number=1,
        fee_status_latest="PAID",
        fee_percentage_paid=100.0,
        fee_terms_overdue=0,
        fee_pending_count=0,
    )

    prob1 = predictor.predict_dropout_probability(feats1)
    prob2 = predictor.predict_dropout_probability(feats1)

    assert prob1 == prob2
    assert prob1 < 0.30  # Healthy student has low dropout probability

def test_global_feature_importances_sum():
    """Verify feature importances are present and sum approximately to 1.0."""
    predictor = MLPredictor(model_path=MODEL_PATH, metadata_path=METADATA_PATH)
    importances = predictor.get_feature_importances()

    assert len(importances) == len(ML_FEATURE_NAMES)
    total_imp = sum(item["importance"] for item in importances)
    assert abs(total_imp - 1.0) < 0.05

def test_missing_model_file_raises_clean_error(tmp_path):
    """Verify missing model file raises FileNotFoundError with actionable message."""
    fake_path = tmp_path / "non_existent.joblib"
    with pytest.raises(FileNotFoundError) as exc_info:
        MLPredictor(model_path=fake_path, metadata_path=METADATA_PATH)
    assert "Trained model artifact not found" in str(exc_info.value)

def test_500_student_inference_sanity_check(synthetic_cohort):
    """Run ML inference over all 500 synthetic students ensuring 0 NaNs and valid probabilities."""
    predictor = MLPredictor(model_path=MODEL_PATH, metadata_path=METADATA_PATH)

    probs = []
    for p in synthetic_cohort:
        feats = FeatureEngineeringService.extract_features(p, reference_date="2026-10-01")
        prob = predictor.predict_dropout_probability(feats)
        assert not math.isnan(prob)
        assert not math.isinf(prob)
        assert 0.0 <= prob <= 1.0
        probs.append(prob)

    assert len(probs) == 500
    assert min(probs) >= 0.0
    assert max(probs) <= 1.0
    assert max(probs) > min(probs)
