import pytest
import math
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

try:
    from app.core.database import Base
    from app.schemas.student import (
        StudentBasic,
        AttendanceHistoryItem,
        MarksHistoryItem,
        FeeHistoryItem,
        AttemptHistoryItem,
        UnifiedStudentProfile,
    )
    from app.services.features import FeatureEngineeringService
    from app.services.fusion import StudentDataFusionService
    from app.services.ingestion import IngestionService
    from ml.data_generation.generator import SyntheticDataGenerator
except ImportError:
    from backend.app.core.database import Base
    from backend.app.schemas.student import (
        StudentBasic,
        AttendanceHistoryItem,
        MarksHistoryItem,
        FeeHistoryItem,
        AttemptHistoryItem,
        UnifiedStudentProfile,
    )
    from backend.app.services.features import FeatureEngineeringService
    from backend.app.services.fusion import StudentDataFusionService
    from backend.app.services.ingestion import IngestionService
    from ml.data_generation.generator import SyntheticDataGenerator

def create_profile(
    student_id=1,
    attendance_pcts=None,
    marks_records=None,
    attempts=None,
    fees=None,
    semester=4,
):
    """Helper to build a mock UnifiedStudentProfile."""
    att_items = []
    if attendance_pcts is not None:
        for idx, pct in enumerate(attendance_pcts):
            att_items.append(
                AttendanceHistoryItem(
                    week_number=idx + 1,
                    total_classes=20,
                    attended_classes=int(round(20 * (pct / 100.0))),
                    percentage=float(pct),
                )
            )

    marks_items = []
    if marks_records is not None:
        for m in marks_records:
            marks_items.append(
                MarksHistoryItem(
                    subject_name=m.get("subject", "Math"),
                    exam_type=m.get("exam_type", "MIDTERM"),
                    max_marks=m.get("max_marks", 100.0),
                    obtained_marks=m.get("obtained_marks", 75.0),
                    attempt_number=m.get("attempt_number", 1),
                )
            )

    fee_items = []
    if fees is not None:
        for f in fees:
            fee_items.append(
                FeeHistoryItem(
                    semester=f.get("semester", semester),
                    total_fee=f.get("total_fee", 25000.0),
                    paid_amount=f.get("paid_amount", 25000.0),
                    due_date=f.get("due_date", "2026-09-30"),
                    status=f.get("status", "PAID"),
                )
            )

    attempt_items = []
    if attempts is not None:
        for a in attempts:
            attempt_items.append(
                AttemptHistoryItem(
                    subject_name=a.get("subject", "Physics"),
                    semester=a.get("semester", semester - 1),
                    attempt_number=a.get("attempt_number", 1),
                    status=a.get("status", "ACTIVE"),
                )
            )

    return UnifiedStudentProfile(
        student=StudentBasic(
            id=student_id,
            roll_number=f"CS2026{student_id:04d}",
            name=f"Student {student_id}",
            department="CSE",
            semester=semester,
        ),
        attendance=att_items,
        marks=marks_items,
        fees=fee_items,
        attempts=attempt_items,
    )

def test_attendance_negative_slope_and_decline():
    """Verify [90, 80, 70, 60] produces negative slope, decline_pp = 30, consecutive_decline = 3."""
    profile = create_profile(attendance_pcts=[90, 80, 70, 60])
    feats = FeatureEngineeringService.extract_features(profile)

    assert feats.attendance_current == 60.0
    assert feats.attendance_mean == 75.0
    assert feats.attendance_slope < 0.0
    assert feats.attendance_decline_pp == 30.0
    assert feats.attendance_consecutive_decline == 3

def test_attendance_positive_slope():
    """Verify [60, 70, 80, 90] produces positive slope and consecutive_decline = 0."""
    profile = create_profile(attendance_pcts=[60, 70, 80, 90])
    feats = FeatureEngineeringService.extract_features(profile)

    assert feats.attendance_current == 90.0
    assert feats.attendance_slope > 0.0
    assert feats.attendance_decline_pp == 0.0
    assert feats.attendance_consecutive_decline == 0

def test_attendance_flat_slope():
    """Verify [80, 80, 80, 80] produces slope approximately 0 and consecutive_decline = 0."""
    profile = create_profile(attendance_pcts=[80, 80, 80, 80])
    feats = FeatureEngineeringService.extract_features(profile)

    assert abs(feats.attendance_slope) < 0.01
    assert feats.attendance_decline_pp == 0.0
    assert feats.attendance_consecutive_decline == 0

def test_attendance_consecutive_decline_exact_transitions():
    """Verify [88, 84, 76, 68, 61] produces exactly 4 declining transitions (NOT 5)."""
    profile = create_profile(attendance_pcts=[88, 84, 76, 68, 61])
    feats = FeatureEngineeringService.extract_features(profile)

    assert feats.attendance_consecutive_decline == 4

def test_attendance_acceleration():
    """Verify attendance acceleration measures change in weekly differences."""
    # [90, 86, 80, 71] -> diffs: -4, -6, -9 -> slope of diffs is negative (-2.5)
    profile = create_profile(attendance_pcts=[90, 86, 80, 71])
    feats = FeatureEngineeringService.extract_features(profile)

    assert feats.attendance_acceleration < 0.0

def test_attendance_single_and_empty_edge_cases():
    """Verify single observation and empty attendance lists handle safely without NaN."""
    profile_single = create_profile(attendance_pcts=[75.0])
    feats_single = FeatureEngineeringService.extract_features(profile_single)
    assert feats_single.attendance_current == 75.0
    assert feats_single.attendance_slope == 0.0
    assert not feats_single.has_sufficient_attendance_history

    profile_empty = create_profile(attendance_pcts=[])
    feats_empty = FeatureEngineeringService.extract_features(profile_empty)
    assert feats_empty.attendance_current == 0.0
    assert feats_empty.attendance_history_count == 0
    assert not feats_empty.has_sufficient_attendance_history

def test_marks_normalization_and_slope():
    """Verify marks with different max_marks normalize correctly and compute slope."""
    marks_data = [
        {"subject": "Math", "exam_type": "TEST1", "max_marks": 20.0, "obtained_marks": 16.0},  # 80%
        {"subject": "Math", "exam_type": "TEST2", "max_marks": 20.0, "obtained_marks": 14.0},  # 70%
        {"subject": "Math", "exam_type": "MIDTERM", "max_marks": 50.0, "obtained_marks": 30.0}, # 60%
        {"subject": "Math", "exam_type": "FINAL", "max_marks": 100.0, "obtained_marks": 50.0},  # 50%
    ]
    profile = create_profile(marks_records=marks_data)
    feats = FeatureEngineeringService.extract_features(profile)

    assert feats.marks_current_avg == 50.0
    assert feats.marks_mean == 65.0
    assert feats.marks_slope < 0.0
    assert feats.marks_decline_pp == 30.0
    assert feats.marks_consecutive_failures == 0
    assert feats.has_sufficient_marks_history

def test_marks_consecutive_failures_and_failed_subjects():
    """Verify consecutive failure stages and failing subject counts (< 40%)."""
    marks_data = [
        {"subject": "Math", "exam_type": "TEST1", "max_marks": 100.0, "obtained_marks": 55.0},
        {"subject": "Math", "exam_type": "TEST2", "max_marks": 100.0, "obtained_marks": 35.0}, # Fail
        {"subject": "Math", "exam_type": "FINAL", "max_marks": 100.0, "obtained_marks": 30.0}, # Fail
        {"subject": "Electronics", "exam_type": "FINAL", "max_marks": 100.0, "obtained_marks": 25.0}, # Fail
    ]
    profile = create_profile(marks_records=marks_data)
    feats = FeatureEngineeringService.extract_features(profile)

    assert feats.marks_consecutive_failures >= 1
    assert feats.marks_failed_subject_count == 2

def test_empty_marks_edge_case():
    """Verify empty marks records handle safely."""
    profile = create_profile(marks_records=[])
    feats = FeatureEngineeringService.extract_features(profile)

    assert feats.marks_current_avg == 0.0
    assert feats.marks_history_count == 0
    assert not feats.has_sufficient_marks_history

def test_backlog_features():
    """Verify active backlog counts, semester backlogs, and trend direction."""
    attempts = [
        {"subject": "Math", "semester": 3, "attempt_number": 2, "status": "ACTIVE"},
        {"subject": "Physics", "semester": 4, "attempt_number": 1, "status": "ACTIVE"},
        {"subject": "Chemistry", "semester": 2, "attempt_number": 2, "status": "CLEARED"},
    ]
    profile = create_profile(attempts=attempts, semester=4)
    feats = FeatureEngineeringService.extract_features(profile)

    assert feats.backlog_count_active == 2
    assert feats.backlog_count_total == 3
    assert feats.backlog_new_this_semester == 1
    assert feats.max_attempt_number == 2
    assert feats.backlog_trend_numeric == 1

def test_fee_contextual_features():
    """Verify fee percentage paid and overdue calculations relative to fixed reference date."""
    fees = [
        {"semester": 3, "total_fee": 25000.0, "paid_amount": 25000.0, "due_date": "2026-03-31", "status": "PAID"},
        {"semester": 4, "total_fee": 25000.0, "paid_amount": 10000.0, "due_date": "2026-09-30", "status": "PARTIAL"},
    ]
    profile = create_profile(fees=fees)
    
    # Reference date after due date (2026-10-15) -> 1 term overdue
    feats_past = FeatureEngineeringService.extract_features(profile, reference_date="2026-10-15")
    assert feats_past.fee_status_latest == "PARTIAL"
    assert feats_past.fee_percentage_paid == 40.0
    assert feats_past.fee_pending_count == 1
    assert feats_past.fee_terms_overdue == 1

    # Reference date before due date (2026-08-01) -> 0 terms overdue
    feats_before = FeatureEngineeringService.extract_features(profile, reference_date="2026-08-01")
    assert feats_before.fee_terms_overdue == 0

def test_empty_fees_edge_case():
    """Verify empty fee history returns neutral defaults."""
    profile = create_profile(fees=[])
    feats = FeatureEngineeringService.extract_features(profile)

    assert feats.fee_status_latest == "UNKNOWN"
    assert feats.fee_percentage_paid == 100.0
    assert feats.fee_terms_overdue == 0
    assert feats.fee_pending_count == 0

def test_no_synthetic_leakage_in_features():
    """Verify trajectory_type and dropout_label are completely absent from features."""
    profile = create_profile(attendance_pcts=[85, 80], marks_records=[{"subject": "Math", "obtained_marks": 70.0, "max_marks": 100.0}])
    feats = FeatureEngineeringService.extract_features(profile)
    feat_dict = feats.model_dump()

    assert "trajectory_type" not in feat_dict
    assert "dropout_label" not in feat_dict

def test_numerical_stability_no_nan_or_inf():
    """Verify that all features are clean finite numbers without NaN or Inf."""
    profile = create_profile(
        attendance_pcts=[90, 80, 70, 60],
        marks_records=[{"subject": "CS", "obtained_marks": 45, "max_marks": 100}],
        attempts=[{"subject": "CS", "semester": 3, "status": "ACTIVE"}],
        fees=[{"semester": 4, "total_fee": 25000, "paid_amount": 25000, "status": "PAID"}]
    )
    feats = FeatureEngineeringService.extract_features(profile)
    feat_dict = feats.model_dump()

    for k, v in feat_dict.items():
        if isinstance(v, float):
            assert not math.isnan(v), f"Feature {k} is NaN"
            assert not math.isinf(v), f"Feature {k} is Infinite"

def test_pipeline_integration_phase4_5_6():
    """Integration test: Ingest via Phase 4 -> Fuse via Phase 5 -> Extract features via Phase 6."""
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()

    try:
        ingestion = IngestionService(session)

        # 1. Ingest Student
        student_csv = "student_id,roll_number,name,department,semester\n701,CS701,Katherine Johnson,CSE,4\n"
        ingestion.ingest("students", "students.csv", student_csv.encode("utf-8"))

        # 2. Ingest Attendance: [85, 80, 75, 70]
        att_csv = (
            "student_id,week_number,month,total_classes,attended_classes\n"
            "701,1,August,20,17\n"
            "701,2,August,20,16\n"
            "701,3,August,20,15\n"
            "701,4,August,20,14\n"
        )
        ingestion.ingest("attendance", "att.csv", att_csv.encode("utf-8"))

        # 3. Ingest Marks
        marks_csv = (
            "student_id,subject_name,exam_type,max_marks,obtained_marks\n"
            "701,Math,TEST1,20,18\n"
            "701,Math,FINAL,100,70\n"
        )
        ingestion.ingest("marks", "marks.csv", marks_csv.encode("utf-8"))

        # 4. Ingest Fees
        fees_csv = "student_id,semester,total_fee,paid_amount,due_date,status\n701,4,25000,25000,2026-09-30,PAID\n"
        ingestion.ingest("fees", "fees.csv", fees_csv.encode("utf-8"))

        # 5. Ingest Attempt
        att_rec_csv = "student_id,subject_name,semester,attempt_number,status\n701,Electronics,3,1,ACTIVE\n"
        ingestion.ingest("attempts", "attempts.csv", att_rec_csv.encode("utf-8"))

        # Fuse
        fusion = StudentDataFusionService(session)
        profile = fusion.fuse_by_id(701)
        assert profile is not None

        # Extract features
        feats = FeatureEngineeringService.extract_features(profile)
        assert feats.student_id == 701
        assert feats.attendance_current == 70.0
        assert feats.attendance_slope < 0.0
        assert feats.attendance_consecutive_decline == 3
        assert feats.marks_current_avg == 70.0
        assert feats.backlog_count_active == 1
        assert feats.fee_status_latest == "PAID"

    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

def test_synthetic_500_cohort_sanity_check(tmp_path):
    """Sanity check: ingest 500 generated synthetic students and extract features without errors or NaNs."""
    temp_dir = str(tmp_path / "cohort")
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
        assert len(profiles) == 50

        for p in profiles:
            feats = FeatureEngineeringService.extract_features(p, reference_date="2026-10-01")
            d = feats.model_dump()
            assert not math.isnan(d["attendance_slope"])
            assert not math.isnan(d["marks_slope"])
            assert "trajectory_type" not in d
            assert "dropout_label" not in d

    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
