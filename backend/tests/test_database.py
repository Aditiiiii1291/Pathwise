import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
        RiskSnapshot,
        RiskTierEnum,
        TrendEnum,
        Intervention,
        InterventionTypeEnum,
        InterventionStatusEnum,
        InterventionOutcomeEnum,
        RuleConfig,
        Notification,
        NotificationTypeEnum,
        RecipientTypeEnum,
        NotificationStatusEnum,
    )
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
        RiskSnapshot,
        RiskTierEnum,
        TrendEnum,
        Intervention,
        InterventionTypeEnum,
        InterventionStatusEnum,
        InterventionOutcomeEnum,
        RuleConfig,
        Notification,
        NotificationTypeEnum,
        RecipientTypeEnum,
        NotificationStatusEnum,
    )

@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh in-memory SQLite database and session for each test."""
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

def test_database_table_creation(db_session):
    """Verify that all 10 model tables are created."""
    tables = Base.metadata.tables.keys()
    expected_tables = {
        "mentors",
        "students",
        "attendance_records",
        "marks_records",
        "fee_records",
        "attempt_records",
        "risk_snapshots",
        "interventions",
        "rule_configs",
        "notifications",
    }
    assert expected_tables.issubset(set(tables))

def test_mentor_and_student_creation(db_session):
    """Verify Mentor and Student insertion with ForeignKey and relationship."""
    mentor = Mentor(
        name="Dr. Alan Turing",
        email="alan.turing@polytech.edu",
        department="Computer Science",
        phone="+919876543210"
    )
    db_session.add(mentor)
    db_session.commit()
    db_session.refresh(mentor)

    assert mentor.id is not None
    assert mentor.email == "alan.turing@polytech.edu"

    student = Student(
        roll_number="CS2026001",
        name="Ada Lovelace",
        department="Computer Science",
        semester=4,
        guardian_name="Lord Byron",
        guardian_phone="+919123456789",
        guardian_email="byron@example.com",
        mentor_id=mentor.id,
        enrollment_year=2024
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    assert student.id is not None
    assert student.roll_number == "CS2026001"
    assert student.mentor.name == "Dr. Alan Turing"
    assert len(mentor.students) == 1
    assert mentor.students[0].name == "Ada Lovelace"

def test_attendance_record_creation(db_session):
    """Verify AttendanceRecord creation and association with Student."""
    student = Student(roll_number="CS2026002", name="Grace Hopper", department="CS", semester=3)
    db_session.add(student)
    db_session.commit()

    attendance = AttendanceRecord(
        student_id=student.id,
        week_number=1,
        month="August",
        total_classes=20,
        attended_classes=18,
        percentage=90.0
    )
    db_session.add(attendance)
    db_session.commit()
    db_session.refresh(attendance)

    assert attendance.id is not None
    assert attendance.percentage == 90.0
    assert attendance.student.name == "Grace Hopper"
    assert len(student.attendance_records) == 1

def test_marks_record_creation(db_session):
    """Verify MarksRecord creation with ExamTypeEnum."""
    student = Student(roll_number="CS2026003", name="Claude Shannon", department="ECE", semester=5)
    db_session.add(student)
    db_session.commit()

    marks = MarksRecord(
        student_id=student.id,
        subject_name="Information Theory",
        exam_type=ExamTypeEnum.MIDTERM,
        max_marks=100.0,
        obtained_marks=88.5,
        attempt_number=1
    )
    db_session.add(marks)
    db_session.commit()
    db_session.refresh(marks)

    assert marks.id is not None
    assert marks.exam_type == ExamTypeEnum.MIDTERM
    assert marks.obtained_marks == 88.5
    assert len(student.marks_records) == 1

def test_fee_record_creation(db_session):
    """Verify FeeRecord creation with FeeStatusEnum."""
    student = Student(roll_number="CS2026004", name="John von Neumann", department="ME", semester=2)
    db_session.add(student)
    db_session.commit()

    fee = FeeRecord(
        student_id=student.id,
        semester=2,
        total_fee=25000.0,
        paid_amount=15000.0,
        due_date="2026-09-30",
        status=FeeStatusEnum.PARTIAL
    )
    db_session.add(fee)
    db_session.commit()
    db_session.refresh(fee)

    assert fee.id is not None
    assert fee.status == FeeStatusEnum.PARTIAL
    assert fee.paid_amount == 15000.0
    assert len(student.fee_records) == 1

def test_attempt_backlog_record_creation(db_session):
    """Verify AttemptRecord creation with BacklogStatusEnum."""
    student = Student(roll_number="CS2026005", name="Margaret Hamilton", department="CS", semester=6)
    db_session.add(student)
    db_session.commit()

    attempt = AttemptRecord(
        student_id=student.id,
        subject_name="Operating Systems",
        semester=5,
        attempt_number=2,
        status=BacklogStatusEnum.ACTIVE
    )
    db_session.add(attempt)
    db_session.commit()
    db_session.refresh(attempt)

    assert attempt.id is not None
    assert attempt.status == BacklogStatusEnum.ACTIVE
    assert attempt.attempt_number == 2
    assert len(student.attempt_records) == 1

def test_risk_snapshot_creation(db_session):
    """Verify RiskSnapshot creation with RiskTierEnum and TrendEnum."""
    student = Student(roll_number="CS2026006", name="Donald Knuth", department="CS", semester=4)
    db_session.add(student)
    db_session.commit()

    snapshot = RiskSnapshot(
        student_id=student.id,
        rule_score=65.0,
        ml_probability=0.72,
        final_score=68.5,
        risk_tier=RiskTierEnum.HIGH,
        trend=TrendEnum.GRADUALLY_DETERIORATING,
        factors_json=["Attendance dropped by 18 pp", "1 active backlog"],
        feature_imp_json={"attendance_slope": 0.45, "marks_slope": 0.35},
        recommendations_json=["Mentor counselling recommended", "Attendance recovery plan"]
    )
    db_session.add(snapshot)
    db_session.commit()
    db_session.refresh(snapshot)

    assert snapshot.id is not None
    assert snapshot.risk_tier == RiskTierEnum.HIGH
    assert snapshot.trend == TrendEnum.GRADUALLY_DETERIORATING
    assert len(snapshot.factors_json) == 2
    assert len(student.risk_snapshots) == 1

def test_intervention_creation(db_session):
    """Verify Intervention creation referencing student and mentor."""
    mentor = Mentor(name="Dr. Katherine Johnson", email="kjohnson@polytech.edu", department="Math")
    db_session.add(mentor)
    db_session.commit()

    student = Student(roll_number="CS2026007", name="Dorothy Vaughan", department="Math", semester=3, mentor_id=mentor.id)
    db_session.add(student)
    db_session.commit()

    intervention = Intervention(
        student_id=student.id,
        mentor_id=mentor.id,
        type=InterventionTypeEnum.COUNSELLING,
        notes="Discussed study schedules and academic support options.",
        risk_score_before=72.0,
        status=InterventionStatusEnum.COMPLETED,
        outcome=InterventionOutcomeEnum.IMPROVED,
        risk_score_after=45.0
    )
    db_session.add(intervention)
    db_session.commit()
    db_session.refresh(intervention)

    assert intervention.id is not None
    assert intervention.type == InterventionTypeEnum.COUNSELLING
    assert intervention.status == InterventionStatusEnum.COMPLETED
    assert intervention.outcome == InterventionOutcomeEnum.IMPROVED
    assert intervention.student.name == "Dorothy Vaughan"
    assert intervention.mentor.name == "Dr. Katherine Johnson"
    assert len(student.interventions) == 1
    assert len(mentor.interventions) == 1

def test_rule_config_creation(db_session):
    """Verify RuleConfig creation with department and config JSON."""
    rule_config = RuleConfig(
        department="Computer Science",
        config_json={
            "attendance_threshold": 75.0,
            "marks_threshold": 40.0,
            "weights": {"attendance": 0.35, "marks": 0.35, "backlogs": 0.20, "fees": 0.10}
        },
        updated_by="HOD_CS"
    )
    db_session.add(rule_config)
    db_session.commit()
    db_session.refresh(rule_config)

    assert rule_config.id is not None
    assert rule_config.department == "Computer Science"
    assert rule_config.config_json["attendance_threshold"] == 75.0

def test_notification_creation(db_session):
    """Verify Notification creation with type and recipient enums."""
    student = Student(roll_number="CS2026008", name="Mary Jackson", department="ME", semester=1)
    db_session.add(student)
    db_session.commit()

    notification = Notification(
        student_id=student.id,
        type=NotificationTypeEnum.MOCK,
        recipient_type=RecipientTypeEnum.GUARDIAN,
        recipient_email="guardian.mary@example.com",
        subject="Academic Attendance Notification",
        body="Your ward's attendance for the recent period requires attention.",
        status=NotificationStatusEnum.SENT
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    assert notification.id is not None
    assert notification.recipient_type == RecipientTypeEnum.GUARDIAN
    assert notification.type == NotificationTypeEnum.MOCK
    assert notification.status == NotificationStatusEnum.SENT
    assert len(student.notifications) == 1
