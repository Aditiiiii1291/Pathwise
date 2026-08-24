import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

try:
    from app.core.database import Base
    from app.models import (
        Student,
        Mentor,
        AttendanceRecord,
        MarksRecord,
        ExamTypeEnum,
        FeeRecord,
        FeeStatusEnum,
        AttemptRecord,
        BacklogStatusEnum,
    )
    from app.services.fusion import StudentDataFusionService
    from app.services.ingestion import IngestionService
except ImportError:
    from backend.app.core.database import Base
    from backend.app.models import (
        Student,
        Mentor,
        AttendanceRecord,
        MarksRecord,
        ExamTypeEnum,
        FeeRecord,
        FeeStatusEnum,
        AttemptRecord,
        BacklogStatusEnum,
    )
    from backend.app.services.fusion import StudentDataFusionService
    from backend.app.services.ingestion import IngestionService

@pytest.fixture(scope="function")
def db_session():
    """Isolated in-memory SQLite database session using StaticPool."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

def test_fuse_full_student_profile(db_session):
    """Verify fusion of complete student profile with mentor and all academic histories."""
    mentor = Mentor(name="Prof. Charles Babbage", email="babbage@polytech.edu", department="CSE", phone="+919876543210")
    db_session.add(mentor)
    db_session.commit()

    student = Student(
        id=1,
        roll_number="CSE2026001",
        name="Ada Lovelace",
        department="CSE",
        semester=4,
        guardian_name="Lord Byron",
        guardian_phone="+919000000001",
        guardian_email="byron@example.test",
        mentor_id=mentor.id,
        enrollment_year=2024
    )
    db_session.add(student)
    db_session.commit()

    # Out of order attendance
    db_session.add(AttendanceRecord(student_id=1, week_number=3, total_classes=20, attended_classes=18, percentage=90.0))
    db_session.add(AttendanceRecord(student_id=1, week_number=1, total_classes=20, attended_classes=16, percentage=80.0))
    db_session.add(AttendanceRecord(student_id=1, week_number=2, total_classes=20, attended_classes=17, percentage=85.0))

    # Out of order marks
    db_session.add(MarksRecord(student_id=1, subject_name="Mathematics", exam_type=ExamTypeEnum.FINAL, max_marks=100.0, obtained_marks=92.0))
    db_session.add(MarksRecord(student_id=1, subject_name="Mathematics", exam_type=ExamTypeEnum.TEST1, max_marks=20.0, obtained_marks=18.0))
    db_session.add(MarksRecord(student_id=1, subject_name="Mathematics", exam_type=ExamTypeEnum.MIDTERM, max_marks=50.0, obtained_marks=45.0))

    # Fees
    db_session.add(FeeRecord(student_id=1, semester=3, total_fee=25000.0, paid_amount=25000.0, status=FeeStatusEnum.PAID))
    db_session.add(FeeRecord(student_id=1, semester=4, total_fee=25000.0, paid_amount=15000.0, status=FeeStatusEnum.PARTIAL))

    # Attempts
    db_session.add(AttemptRecord(student_id=1, subject_name="Electronics", semester=2, attempt_number=2, status=BacklogStatusEnum.CLEARED))

    db_session.commit()

    service = StudentDataFusionService(db_session)
    profile = service.fuse_by_id(1)

    assert profile is not None
    assert profile.student.name == "Ada Lovelace"
    assert profile.student.roll_number == "CSE2026001"
    assert profile.student.mentor is not None
    assert profile.student.mentor.name == "Prof. Charles Babbage"

    # Attendance sorted chronologically (1, 2, 3)
    assert len(profile.attendance) == 3
    assert [a.week_number for a in profile.attendance] == [1, 2, 3]
    assert profile.attendance[0].percentage == 80.0

    # Marks sorted deterministically by exam sequence (TEST1 -> MIDTERM -> FINAL)
    assert len(profile.marks) == 3
    assert [m.exam_type for m in profile.marks] == ["TEST1", "MIDTERM", "FINAL"]

    # Fees sorted by semester (3, 4)
    assert len(profile.fees) == 2
    assert [f.semester for f in profile.fees] == [3, 4]
    assert profile.fees[0].status == "PAID"
    assert profile.fees[1].status == "PARTIAL"

    # Attempts sorted
    assert len(profile.attempts) == 1
    assert profile.attempts[0].subject_name == "Electronics"
    assert profile.attempts[0].status == "CLEARED"

    # Non-analytical metadata counts
    assert profile.attendance_record_count == 3
    assert profile.marks_record_count == 3
    assert profile.fee_record_count == 2
    assert profile.attempt_record_count == 1

def test_missing_sections_return_empty_lists(db_session):
    """Verify empty sections return empty lists and no fake data is generated."""
    student = Student(id=2, roll_number="ECE2026002", name="Grace Hopper", department="ECE", semester=2)
    db_session.add(student)
    db_session.commit()

    service = StudentDataFusionService(db_session)
    profile = service.fuse_by_id(2)

    assert profile is not None
    assert profile.student.name == "Grace Hopper"
    assert profile.student.mentor is None
    assert profile.attendance == []
    assert profile.marks == []
    assert profile.fees == []
    assert profile.attempts == []
    assert profile.attendance_record_count == 0
    assert profile.marks_record_count == 0
    assert profile.fee_record_count == 0
    assert profile.attempt_record_count == 0

def test_lookup_by_roll_number(db_session):
    """Verify lookup by institutional roll number."""
    student = Student(id=3, roll_number="ME2026003", name="James Watt", department="ME", semester=3)
    db_session.add(student)
    db_session.commit()

    service = StudentDataFusionService(db_session)
    profile = service.fuse_by_roll_number("ME2026003")

    assert profile is not None
    assert profile.student.id == 3
    assert profile.student.roll_number == "ME2026003"

def test_unknown_student_returns_none(db_session):
    """Verify non-existent student IDs and roll numbers return None without throwing errors."""
    service = StudentDataFusionService(db_session)
    assert service.fuse_by_id(99999) is None
    assert service.fuse_by_roll_number("UNKNOWN_ROLL") is None

def test_no_synthetic_leakage(db_session):
    """Verify synthetic development fields (trajectory_type, dropout_label) are not in unified profile."""
    student = Student(id=4, roll_number="CE2026004", name="Thomas Telford", department="CE", semester=1)
    db_session.add(student)
    db_session.commit()

    service = StudentDataFusionService(db_session)
    profile = service.fuse_by_id(4)

    profile_dict = profile.model_dump()
    assert "trajectory_type" not in profile_dict["student"]
    assert "dropout_label" not in profile_dict["student"]
    assert "trajectory_type" not in profile_dict
    assert "dropout_label" not in profile_dict

def test_integration_with_ingestion_pipeline(db_session):
    """Integration test: ingest multi-table records via IngestionService and fuse into one profile."""
    ingestion = IngestionService(db_session)

    # 1. Ingest Student
    student_csv = "student_id,roll_number,name,department,semester\n501,CS501,Hedy Lamarr,CSE,4\n"
    summary1 = ingestion.ingest("students", "students.csv", student_csv.encode("utf-8"))
    assert summary1.inserted_rows == 1

    # 2. Ingest Attendance
    att_csv = "student_id,week_number,month,total_classes,attended_classes\n501,1,August,20,18\n501,2,August,20,19\n"
    summary2 = ingestion.ingest("attendance", "att.csv", att_csv.encode("utf-8"))
    assert summary2.inserted_rows == 2

    # 3. Ingest Marks
    marks_csv = "student_id,subject_name,exam_type,max_marks,obtained_marks\n501,Programming,Test1,20,19\n501,Programming,Final,100,88\n"
    summary3 = ingestion.ingest("marks", "marks.csv", marks_csv.encode("utf-8"))
    assert summary3.inserted_rows == 2

    # 4. Ingest Fees
    fees_csv = "student_id,semester,total_fee,paid_amount,due_date,status\n501,4,25000,25000,2026-09-30,PAID\n"
    summary4 = ingestion.ingest("fees", "fees.csv", fees_csv.encode("utf-8"))
    assert summary4.inserted_rows == 1

    # 5. Ingest Attempt
    attempts_csv = "student_id,subject_name,semester,attempt_number,status\n501,Electronics,3,1,CLEARED\n"
    summary5 = ingestion.ingest("attempts", "attempts.csv", attempts_csv.encode("utf-8"))
    assert summary5.inserted_rows == 1

    # Run Fusion
    fusion = StudentDataFusionService(db_session)
    profile = fusion.fuse_by_id(501)

    assert profile is not None
    assert profile.student.name == "Hedy Lamarr"
    assert len(profile.attendance) == 2
    assert len(profile.marks) == 2
    assert len(profile.fees) == 1
    assert len(profile.attempts) == 1
    assert profile.attendance[0].week_number == 1
    assert profile.marks[0].exam_type == "TEST1"
    assert profile.fees[0].status == "PAID"
    assert profile.attempts[0].status == "CLEARED"
