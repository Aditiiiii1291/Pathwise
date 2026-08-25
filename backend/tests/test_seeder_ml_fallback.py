import pytest
from unittest.mock import patch
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.student import Student
from app.models.risk import RiskSnapshot
from app.scripts.seed_demo_data import seed_academic_cohort
from app.services.ml_predictor import MLPredictor


def test_normal_assessment_requires_real_ml_model():
    """Verify that normal production ML inference strictly raises FileNotFoundError if artifact is missing."""
    fake_path = Path("/tmp/nonexistent_model_dropout_detector.joblib")
    with pytest.raises(FileNotFoundError) as exc_info:
        MLPredictor(model_path=fake_path)
    assert "Trained model artifact not found" in str(exc_info.value)


def test_seeder_fallback_when_model_artifact_absent():
    """
    Verify that when the trained ML model artifact is absent (e.g. inside the Render container),
    seed_academic_cohort gracefully falls back to deterministic rule-derived baseline probabilities,
    creating 500 valid, bounded RiskSnapshot entries.
    """
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()

    try:
        # Simulate missing ML model artifact by mocking MLPredictor constructor to raise FileNotFoundError
        with patch("app.scripts.seed_demo_data.MLPredictor", side_effect=FileNotFoundError("Model artifact missing in container")):
            count = seed_academic_cohort(db)
            assert count == 500
            assert db.query(Student).count() == 500

            snapshots = db.query(RiskSnapshot).all()
            assert len(snapshots) == 500

            for snap in snapshots:
                # Assert bounded values
                assert 0.0 <= snap.ml_probability <= 1.0
                assert 0.0 <= snap.final_score <= 100.0
                assert snap.risk_tier is not None
                assert snap.trend is not None

        # Verify idempotency on second run
        count_second = seed_academic_cohort(db)
        assert count_second == 500
        assert db.query(Student).count() == 500
        assert db.query(RiskSnapshot).count() == 500

    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)
