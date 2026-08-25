import os
import tempfile
import pytest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Test that SyntheticDataGenerator is directly importable from app package (isolated container context)
from app.data_generation.generator import (
    SyntheticDataGenerator,
    TRAJECTORY_DISTRIBUTION,
    DEPARTMENTS,
    SUBJECTS_POOL,
    EXAM_TYPES,
)
from app.core.database import Base
from app.scripts.seed_demo_data import seed_academic_cohort
from app.models.student import Student
from app.models.mentor import Mentor
from app.models.risk import RiskSnapshot


def test_synthetic_data_generator_contract_and_filenames():
    """Verify generator creates all 5 CSVs with required filenames and non-empty records."""
    with tempfile.TemporaryDirectory() as temp_dir:
        gen = SyntheticDataGenerator(num_students=10, seed=123, output_dir=temp_dir)
        gen.generate().save()

        expected_files = [
            "students_roster.csv",
            "attendance.csv",
            "marks.csv",
            "fees.csv",
            "attempts.csv",
            "metadata.json",
        ]

        for fname in expected_files:
            fpath = os.path.join(temp_dir, fname)
            assert os.path.exists(fpath), f"Missing required dataset file: {fname}"

        # Verify roster columns
        roster_df = pd.read_csv(os.path.join(temp_dir, "students_roster.csv"))
        assert len(roster_df) == 10
        assert set(["student_id", "roll_number", "name", "department", "semester"]).issubset(roster_df.columns)

        # Verify attendance columns
        att_df = pd.read_csv(os.path.join(temp_dir, "attendance.csv"))
        assert len(att_df) == 10 * 14
        assert set(["student_id", "week_number", "total_classes", "attended_classes", "percentage"]).issubset(att_df.columns)


def test_seed_academic_cohort_in_isolated_backend_context():
    """
    Verify seed_academic_cohort executes successfully using only the backend app package,
    matching the Render container deployment execution environment.
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
        count = seed_academic_cohort(db)
        assert count == 500
        assert db.query(Student).count() == 500
        assert db.query(Mentor).count() == 1
        assert db.query(RiskSnapshot).count() == 500

        # Verify idempotency on immediate second run
        count_second = seed_academic_cohort(db)
        assert count_second == 500
        assert db.query(Student).count() == 500
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)
