import os
import json
import pytest
import pandas as pd
import numpy as np

from ml.data_generation.generator import SyntheticDataGenerator, TRAJECTORY_DISTRIBUTION

@pytest.fixture(scope="module")
def synthetic_data(tmp_path_factory):
    """Generates a synthetic cohort in a temporary directory for testing."""
    temp_dir = str(tmp_path_factory.mktemp("synthetic_data"))
    gen = SyntheticDataGenerator(num_students=500, seed=42, output_dir=temp_dir)
    gen.generate().save()
    return {
        "output_dir": temp_dir,
        "roster": pd.read_csv(os.path.join(temp_dir, "students_roster.csv")),
        "attendance": pd.read_csv(os.path.join(temp_dir, "attendance.csv")),
        "marks": pd.read_csv(os.path.join(temp_dir, "marks.csv")),
        "fees": pd.read_csv(os.path.join(temp_dir, "fees.csv")),
        "attempts": pd.read_csv(os.path.join(temp_dir, "attempts.csv")),
        "metadata_path": os.path.join(temp_dir, "metadata.json"),
    }

def test_default_student_count(synthetic_data):
    """Verify exactly 500 students are generated."""
    assert len(synthetic_data["roster"]) == 500

def test_unique_identifiers(synthetic_data):
    """Verify student_id and roll_number are unique."""
    roster = synthetic_data["roster"]
    assert roster["student_id"].nunique() == 500
    assert roster["roll_number"].nunique() == 500

def test_relational_integrity(synthetic_data):
    """Verify all child records reference valid student_ids."""
    roster_ids = set(synthetic_data["roster"]["student_id"])
    
    assert set(synthetic_data["attendance"]["student_id"]).issubset(roster_ids)
    assert set(synthetic_data["marks"]["student_id"]).issubset(roster_ids)
    assert set(synthetic_data["fees"]["student_id"]).issubset(roster_ids)
    assert set(synthetic_data["attempts"]["student_id"]).issubset(roster_ids)

def test_attendance_bounds_and_math(synthetic_data):
    """Verify attendance math and boundary constraints."""
    att = synthetic_data["attendance"]
    assert (att["attended_classes"] >= 0).all()
    assert (att["attended_classes"] <= att["total_classes"]).all()
    assert (att["percentage"] >= 0.0).all()
    assert (att["percentage"] <= 100.0).all()

    # Verify percentage mathematically corresponds to attended / total
    calc_pct = np.round((att["attended_classes"] / att["total_classes"]) * 100.0, 2)
    np.testing.assert_allclose(att["percentage"], calc_pct, atol=0.01)

def test_marks_bounds(synthetic_data):
    """Verify marks constraints."""
    marks = synthetic_data["marks"]
    assert (marks["obtained_marks"] >= 0.0).all()
    assert (marks["obtained_marks"] <= marks["max_marks"]).all()
    assert (marks["attempt_number"] >= 1).all()

def test_fee_bounds_and_status(synthetic_data):
    """Verify fee bounds and status consistency."""
    fees = synthetic_data["fees"]
    assert (fees["paid_amount"] >= 0.0).all()
    assert (fees["paid_amount"] <= fees["total_fee"]).all()

    paid_records = fees[fees["status"] == "PAID"]
    assert (paid_records["paid_amount"] == paid_records["total_fee"]).all()

    pending_records = fees[fees["status"] == "PENDING"]
    assert (pending_records["paid_amount"] == 0.0).all()

def test_attempt_records(synthetic_data):
    """Verify backlog/attempt record rules."""
    attempts = synthetic_data["attempts"]
    assert (attempts["attempt_number"] >= 1).all()
    assert set(attempts["status"].unique()).issubset({"ACTIVE", "CLEARED"})

def test_all_six_trajectories_exist(synthetic_data):
    """Verify all six trajectory types are represented."""
    roster = synthetic_data["roster"]
    trajectories = set(roster["trajectory_type"].unique())
    expected = set(TRAJECTORY_DISTRIBUTION.keys())
    assert trajectories == expected

def test_no_null_required_fields(synthetic_data):
    """Verify no nulls in required columns."""
    roster = synthetic_data["roster"]
    assert not roster["student_id"].isnull().any()
    assert not roster["roll_number"].isnull().any()
    assert not roster["name"].isnull().any()
    assert not roster["department"].isnull().any()
    assert not roster["semester"].isnull().any()
    assert not roster["trajectory_type"].isnull().any()
    assert not roster["dropout_label"].isnull().any()

def test_synthetic_identity_format(synthetic_data):
    """Verify identities are explicitly synthetic."""
    roster = synthetic_data["roster"]
    assert roster["name"].str.startswith("Student ").all()
    assert roster["guardian_name"].str.startswith("Guardian ").all()
    assert roster["guardian_email"].str.endswith("@example.test").all()

def test_financial_context_dropout_policy(synthetic_data):
    """Verify financial-context-only students are not penalized with high dropout labels."""
    roster = synthetic_data["roster"]
    fin_students = roster[roster["trajectory_type"] == "FINANCIAL_CONTEXT_ONLY"]
    
    # Financial context students should have a very low synthetic dropout rate (< 20%)
    dropout_rate = fin_students["dropout_label"].mean()
    assert dropout_rate < 0.20, f"Financial context dropout rate unexpectedly high: {dropout_rate}"

def test_reproducibility_with_seed(tmp_path):
    """Verify same seed generates identical dataframes."""
    dir1 = str(tmp_path / "seed42_a")
    dir2 = str(tmp_path / "seed42_b")

    gen1 = SyntheticDataGenerator(num_students=50, seed=42, output_dir=dir1).generate()
    gen2 = SyntheticDataGenerator(num_students=50, seed=42, output_dir=dir2).generate()

    pd.testing.assert_frame_equal(gen1.students_df, gen2.students_df)
    pd.testing.assert_frame_equal(gen1.attendance_df, gen2.attendance_df)
    pd.testing.assert_frame_equal(gen1.marks_df, gen2.marks_df)

def test_different_seed_changes_data(tmp_path):
    """Verify different seeds produce different data."""
    dir1 = str(tmp_path / "seed42")
    dir2 = str(tmp_path / "seed99")

    gen1 = SyntheticDataGenerator(num_students=50, seed=42, output_dir=dir1).generate()
    gen2 = SyntheticDataGenerator(num_students=50, seed=99, output_dir=dir2).generate()

    assert not gen1.students_df["name"].equals(gen2.students_df["name"]) or not gen1.students_df["roll_number"].equals(gen2.students_df["roll_number"])

def test_metadata_file_validity(synthetic_data):
    """Verify metadata.json structure and warnings."""
    meta_path = synthetic_data["metadata_path"]
    assert os.path.exists(meta_path)

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["num_students"] == 500
    assert meta["seed"] == 42
    assert "warning" in meta
    assert "synthetic" in meta["warning"].lower()
    assert meta["row_counts"]["students_roster"] == 500

def test_trajectory_temporal_behavior(synthetic_data):
    """Verify aggregate temporal trends across trajectory cohorts."""
    roster = synthetic_data["roster"]
    att = synthetic_data["attendance"]

    merged = att.merge(roster[["student_id", "trajectory_type"]], on="student_id")

    # Group by trajectory and week, calculate average attendance percentage
    weekly_avg = merged.groupby(["trajectory_type", "week_number"])["percentage"].mean().unstack(level=0)

    # Week 1 vs Week 14 differences
    w1 = weekly_avg.loc[1]
    w14 = weekly_avg.loc[14]

    # Improving: Week 14 > Week 1
    assert w14["IMPROVING"] > w1["IMPROVING"] + 10.0, "Improving cohort did not show upward trend"

    # Gradually Deteriorating: Week 14 < Week 1
    assert w14["GRADUALLY_DETERIORATING"] < w1["GRADUALLY_DETERIORATING"] - 10.0, "Gradually deteriorating cohort did not decline"

    # Rapidly Deteriorating: Week 14 < Week 1 (steeper drop than gradually deteriorating)
    rapid_drop = w1["RAPIDLY_DETERIORATING"] - w14["RAPIDLY_DETERIORATING"]
    gradual_drop = w1["GRADUALLY_DETERIORATING"] - w14["GRADUALLY_DETERIORATING"]
    assert rapid_drop > gradual_drop, "Rapidly deteriorating cohort drop should be steeper than gradual"

    # Academic Distress Only: Attendance remains relatively high throughout
    assert weekly_avg["ACADEMIC_DISTRESS_ONLY"].mean() > 75.0, "Academic distress cohort attendance dropped unexpectedly"
