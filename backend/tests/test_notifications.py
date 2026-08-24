import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.student import Student
from app.models.mentor import Mentor
from app.models.risk import RiskSnapshot, RiskTierEnum, TrendEnum
from app.models.notification import Notification, NotificationTypeEnum, NotificationSeverityEnum
from app.services.notifications import NotificationService

@pytest.fixture(scope="function")
def db_session():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()

    mentor = Mentor(id=1, name="Dr. Alan Turing", email="turing@institute.edu", department="CSE")
    session.add(mentor)
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_student(db_session: Session):
    student = Student(
        id=1,
        roll_number="NOTIF2026001",
        name="Test Notification Student",
        department="CSE",
        semester=3,
        mentor_id=1,
        guardian_name="Guardian Person",
        guardian_email="guardian@example.com",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student

def test_notification_model_creation(db_session: Session, sample_student: Student):
    """Test 1: Basic notification model creation."""
    notif = Notification(
        student_id=sample_student.id,
        notification_type=NotificationTypeEnum.RISK_ESCALATION.value,
        severity=NotificationSeverityEnum.HIGH.value,
        title="Student escalated to High",
        message="Risk score reached 65.0.",
        is_read=False,
    )
    db_session.add(notif)
    db_session.commit()
    db_session.refresh(notif)

    assert notif.id is not None
    assert notif.student_id == sample_student.id
    assert notif.severity == "HIGH"
    assert notif.is_read is False
    assert notif.created_at is not None

def test_initial_high_escalation_creates_notification(db_session: Session, sample_student: Student):
    """Test 2: Initial snapshot with HIGH tier creates HIGH notification."""
    snapshot = RiskSnapshot(
        student_id=sample_student.id,
        rule_score=60.0,
        ml_probability=0.65,
        final_score=62.5,
        risk_tier=RiskTierEnum.HIGH,
        trend=TrendEnum.STABLE,
    )
    db_session.add(snapshot)
    db_session.commit()
    db_session.refresh(snapshot)

    notifs = NotificationService.evaluate_and_create_notifications(db_session, sample_student.id, snapshot)
    assert len(notifs) == 1
    assert notifs[0].severity == "HIGH"
    assert notifs[0].notification_type == NotificationTypeEnum.RISK_ESCALATION.value
    assert "High" in notifs[0].title

def test_initial_critical_escalation_creates_notification(db_session: Session, sample_student: Student):
    """Test 3: Initial snapshot with CRITICAL tier creates CRITICAL notification."""
    snapshot = RiskSnapshot(
        student_id=sample_student.id,
        rule_score=85.0,
        ml_probability=0.88,
        final_score=86.5,
        risk_tier=RiskTierEnum.CRITICAL,
        trend=TrendEnum.STABLE,
    )
    db_session.add(snapshot)
    db_session.commit()
    db_session.refresh(snapshot)

    notifs = NotificationService.evaluate_and_create_notifications(db_session, sample_student.id, snapshot)
    assert len(notifs) == 1
    assert notifs[0].severity == "CRITICAL"
    assert notifs[0].notification_type == NotificationTypeEnum.CRITICAL_RISK.value
    assert "Critical" in notifs[0].title

def test_unchanged_critical_does_not_duplicate(db_session: Session, sample_student: Student):
    """Test 4: Subsequent snapshot with same CRITICAL tier does NOT duplicate alert."""
    # First snapshot: CRITICAL
    snap1 = RiskSnapshot(
        student_id=sample_student.id,
        rule_score=80.0,
        ml_probability=0.82,
        final_score=81.0,
        risk_tier=RiskTierEnum.CRITICAL,
        trend=TrendEnum.STABLE,
    )
    db_session.add(snap1)
    db_session.commit()
    db_session.refresh(snap1)
    notifs1 = NotificationService.evaluate_and_create_notifications(db_session, sample_student.id, snap1)
    assert len(notifs1) == 1

    # Second snapshot: still CRITICAL
    snap2 = RiskSnapshot(
        student_id=sample_student.id,
        rule_score=82.0,
        ml_probability=0.84,
        final_score=83.0,
        risk_tier=RiskTierEnum.CRITICAL,
        trend=TrendEnum.STABLE,
    )
    db_session.add(snap2)
    db_session.commit()
    db_session.refresh(snap2)
    notifs2 = NotificationService.evaluate_and_create_notifications(db_session, sample_student.id, snap2)
    assert len(notifs2) == 0  # Deduplicated!

def test_rapid_deterioration_transition_creates_notification(db_session: Session, sample_student: Student):
    """Test 5: Transition from STABLE to RAPIDLY_DETERIORATING creates alert."""
    snap1 = RiskSnapshot(
        student_id=sample_student.id,
        rule_score=30.0,
        ml_probability=0.20,
        final_score=25.0,
        risk_tier=RiskTierEnum.LOW,
        trend=TrendEnum.STABLE,
    )
    db_session.add(snap1)
    db_session.commit()
    db_session.refresh(snap1)

    # Next snapshot: trend shifts to RAPIDLY_DETERIORATING
    snap2 = RiskSnapshot(
        student_id=sample_student.id,
        rule_score=35.0,
        ml_probability=0.30,
        final_score=32.5,
        risk_tier=RiskTierEnum.LOW,
        trend=TrendEnum.RAPIDLY_DETERIORATING,
    )
    db_session.add(snap2)
    db_session.commit()
    db_session.refresh(snap2)

    notifs = NotificationService.evaluate_and_create_notifications(db_session, sample_student.id, snap2)
    assert len(notifs) == 1
    assert notifs[0].notification_type == NotificationTypeEnum.RAPID_DETERIORATION.value
    assert notifs[0].severity == "HIGH"

def test_unchanged_rapid_deterioration_does_not_duplicate(db_session: Session, sample_student: Student):
    """Test 6: Remaining in RAPIDLY_DETERIORATING does NOT duplicate alert."""
    snap1 = RiskSnapshot(
        student_id=sample_student.id,
        rule_score=40.0,
        ml_probability=0.40,
        final_score=40.0,
        risk_tier=RiskTierEnum.MEDIUM,
        trend=TrendEnum.RAPIDLY_DETERIORATING,
    )
    db_session.add(snap1)
    db_session.commit()
    db_session.refresh(snap1)
    NotificationService.evaluate_and_create_notifications(db_session, sample_student.id, snap1)

    # Subsequent snapshot: still RAPIDLY_DETERIORATING
    snap2 = RiskSnapshot(
        student_id=sample_student.id,
        rule_score=42.0,
        ml_probability=0.42,
        final_score=42.0,
        risk_tier=RiskTierEnum.MEDIUM,
        trend=TrendEnum.RAPIDLY_DETERIORATING,
    )
    db_session.add(snap2)
    db_session.commit()
    db_session.refresh(snap2)

    notifs2 = NotificationService.evaluate_and_create_notifications(db_session, sample_student.id, snap2)
    assert len(notifs2) == 0

def test_risk_improvement_creates_informational_notification(db_session: Session, sample_student: Student):
    """Test 7: Improvement from HIGH to MEDIUM generates INFO notification."""
    snap1 = RiskSnapshot(
        student_id=sample_student.id,
        rule_score=65.0,
        ml_probability=0.60,
        final_score=62.5,
        risk_tier=RiskTierEnum.HIGH,
        trend=TrendEnum.STABLE,
    )
    db_session.add(snap1)
    db_session.commit()
    db_session.refresh(snap1)

    snap2 = RiskSnapshot(
        student_id=sample_student.id,
        rule_score=35.0,
        ml_probability=0.35,
        final_score=35.0,
        risk_tier=RiskTierEnum.MEDIUM,
        trend=TrendEnum.STABLE,
    )
    db_session.add(snap2)
    db_session.commit()
    db_session.refresh(snap2)

    notifs = NotificationService.evaluate_and_create_notifications(db_session, sample_student.id, snap2)
    assert len(notifs) == 1
    assert notifs[0].severity == "INFO"
    assert notifs[0].notification_type == NotificationTypeEnum.RISK_IMPROVEMENT.value
    assert "improved" in notifs[0].title.lower()

def test_get_notifications_api(client, db_session: Session, sample_student: Student):
    """Test 8: GET /api/notifications returns list."""
    notif = Notification(
        student_id=sample_student.id,
        notification_type="RISK_ESCALATION",
        severity="WARNING",
        title="Test Alert",
        message="Test alert message",
        is_read=False,
    )
    db_session.add(notif)
    db_session.commit()

    response = client.get("/api/notifications")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1
    assert "unread_count" in data

def test_notifications_pagination(client, db_session: Session, sample_student: Student):
    """Test 9: Pagination limit and page count work."""
    for i in range(15):
        db_session.add(
            Notification(
                student_id=sample_student.id,
                notification_type="RISK_ESCALATION",
                severity="INFO",
                title=f"Notif {i}",
                message=f"Msg {i}",
                is_read=False,
            )
        )
    db_session.commit()

    response = client.get("/api/notifications?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert data["pages"] >= 3

def test_unread_and_severity_filters(client, db_session: Session, sample_student: Student):
    """Tests 10 & 11: Unread filter and severity filter work."""
    n1 = Notification(
        student_id=sample_student.id,
        notification_type="CRITICAL_RISK",
        severity="CRITICAL",
        title="Critical Alert",
        message="Critical detail",
        is_read=True,
    )
    n2 = Notification(
        student_id=sample_student.id,
        notification_type="RISK_ESCALATION",
        severity="HIGH",
        title="High Alert",
        message="High detail",
        is_read=False,
    )
    db_session.add_all([n1, n2])
    db_session.commit()

    # Unread only
    res_unread = client.get("/api/notifications?unread_only=true")
    assert res_unread.status_code == 200
    unread_items = res_unread.json()["items"]
    assert all(item["is_read"] is False for item in unread_items)

    # Severity filter
    res_crit = client.get("/api/notifications?severity=CRITICAL")
    assert res_crit.status_code == 200
    crit_items = res_crit.json()["items"]
    assert all(item["severity"] == "CRITICAL" for item in crit_items)

def test_unread_count_endpoint(client, db_session: Session, sample_student: Student):
    """Test 12: GET /api/notifications/unread-count returns accurate count."""
    count_before = client.get("/api/notifications/unread-count").json()["unread_count"]

    n = Notification(
        student_id=sample_student.id,
        notification_type="RISK_ESCALATION",
        severity="HIGH",
        title="Unread alert",
        message="Detail",
        is_read=False,
    )
    db_session.add(n)
    db_session.commit()

    count_after = client.get("/api/notifications/unread-count").json()["unread_count"]
    assert count_after == count_before + 1

def test_mark_as_read_endpoints(client, db_session: Session, sample_student: Student):
    """Tests 13 & 14: Mark one as read and mark all as read."""
    n1 = Notification(
        student_id=sample_student.id,
        notification_type="RISK_ESCALATION",
        severity="HIGH",
        title="Alert 1",
        message="Detail 1",
        is_read=False,
    )
    n2 = Notification(
        student_id=sample_student.id,
        notification_type="RISK_ESCALATION",
        severity="HIGH",
        title="Alert 2",
        message="Detail 2",
        is_read=False,
    )
    db_session.add_all([n1, n2])
    db_session.commit()
    db_session.refresh(n1)
    db_session.refresh(n2)

    # Mark single as read
    patch_res = client.patch(f"/api/notifications/{n1.id}/read")
    assert patch_res.status_code == 200
    assert patch_res.json()["is_read"] is True

    # Mark all as read
    patch_all = client.patch("/api/notifications/read-all")
    assert patch_all.status_code == 200
    assert patch_all.json()["success"] is True

    # Check unread count is 0
    count_res = client.get("/api/notifications/unread-count").json()
    assert count_res["unread_count"] == 0

def test_missing_notification_returns_404(client):
    """Test 15: Missing notification ID returns 404."""
    res = client.patch("/api/notifications/9999999/read")
    assert res.status_code == 404

def test_newest_first_ordering(client, db_session: Session, sample_student: Student):
    """Test 16: Notifications returned newest first."""
    n_old = Notification(
        student_id=sample_student.id,
        notification_type="RISK_ESCALATION",
        severity="INFO",
        title="Old Alert",
        message="Old Message",
        is_read=False,
    )
    n_new = Notification(
        student_id=sample_student.id,
        notification_type="RISK_ESCALATION",
        severity="HIGH",
        title="New Alert",
        message="New Message",
        is_read=False,
    )
    db_session.add(n_old)
    db_session.commit()
    db_session.add(n_new)
    db_session.commit()

    res = client.get("/api/notifications?page=1&page_size=20")
    items = res.json()["items"]
    # First item should have highest ID
    assert items[0]["id"] >= items[1]["id"]

def test_get_assessment_does_not_create_notification(client, db_session: Session, sample_student: Student):
    """Test 17: GET /api/students/{id}/assessment remains read-only."""
    count_before = db_session.query(Notification).count()
    res = client.get(f"/api/students/{sample_student.id}/assessment")
    assert res.status_code == 200
    count_after = db_session.query(Notification).count()
    assert count_after == count_before
