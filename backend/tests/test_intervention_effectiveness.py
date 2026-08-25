import pytest
from datetime import datetime, date, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.student import Student
from app.models.mentor import Mentor
from app.models.intervention import Intervention, InterventionStatusEnum
from app.models.risk import RiskSnapshot, RiskTierEnum, TrendEnum
from app.models.notification import Notification
from app.services.intervention_effectiveness import InterventionEffectivenessService


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

    student1 = Student(id=1, roll_number="CS2026001", name="Alice Walker", department="CSE", semester=4, mentor_id=1)
    student2 = Student(id=2, roll_number="CS2026002", name="Bob Martin", department="CSE", semester=3, mentor_id=1)
    session.add_all([student1, student2])
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


def test_baseline_and_post_snapshot_selection(client, db_session: Session):
    """Tests 1, 2, 3, 4: Baseline & post snapshots selected chronologically by computed_at."""
    t_interv = datetime(2026, 8, 10, 12, 0, 0, tzinfo=timezone.utc)

    # Snap 1: before (baseline)
    s1 = RiskSnapshot(
        student_id=1,
        computed_at=datetime(2026, 8, 5, 10, 0, 0, tzinfo=timezone.utc),
        rule_score=75.0,
        ml_probability=0.80,
        final_score=77.0,
        risk_tier=RiskTierEnum.CRITICAL,
        trend=TrendEnum.RAPIDLY_DETERIORATING,
    )
    # Snap 2: even earlier (should not be chosen as baseline)
    s0 = RiskSnapshot(
        student_id=1,
        computed_at=datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc),
        rule_score=60.0,
        ml_probability=0.60,
        final_score=60.0,
        risk_tier=RiskTierEnum.HIGH,
        trend=TrendEnum.STABLE,
    )
    # Snap 3: after
    s2 = RiskSnapshot(
        student_id=1,
        computed_at=datetime(2026, 8, 20, 10, 0, 0, tzinfo=timezone.utc),
        rule_score=40.0,
        ml_probability=0.40,
        final_score=40.0,
        risk_tier=RiskTierEnum.MEDIUM,
        trend=TrendEnum.IMPROVING,
    )
    db_session.add_all([s0, s1, s2])
    db_session.commit()

    interv = Intervention(
        student_id=1,
        title="Weekly Attendance & Tutoring",
        created_at=t_interv,
        status="IN_PROGRESS",
    )
    db_session.add(interv)
    db_session.commit()
    db_session.refresh(interv)

    res = client.get(f"/api/interventions/{interv.id}/effectiveness")
    assert res.status_code == 200
    data = res.json()

    assert data["classification"] == "IMPROVED"
    assert data["before"]["snapshot_id"] == s1.id
    assert data["before"]["score"] == 77.0
    assert data["after"]["snapshot_id"] == s2.id
    assert data["after"]["score"] == 40.0
    assert data["score_delta"] == -37.0
    assert data["tier_transition"] == "CRITICAL → MEDIUM"
    assert data["trend_transition"] == "RAPIDLY_DETERIORATING → IMPROVING"
    assert "decreased" in data["interpretation"]


def test_stability_threshold_and_boundaries(client, db_session: Session):
    """Tests 5, 6, 7, 8: Classification boundaries (delta <= -5.0 -> IMPROVED, >= 5.0 -> WORSENED, else STABLE)."""
    t_interv = datetime(2026, 8, 10, 12, 0, 0, tzinfo=timezone.utc)
    t_before = datetime(2026, 8, 5, 10, 0, 0, tzinfo=timezone.utc)
    t_after = datetime(2026, 8, 15, 10, 0, 0, tzinfo=timezone.utc)

    # Subtest 1: delta = -5.0 -> IMPROVED
    s_base = RiskSnapshot(student_id=1, computed_at=t_before, rule_score=60.0, ml_probability=0.6, final_score=60.0, risk_tier=RiskTierEnum.HIGH, trend=TrendEnum.STABLE)
    s_post1 = RiskSnapshot(student_id=1, computed_at=t_after, rule_score=55.0, ml_probability=0.55, final_score=55.0, risk_tier=RiskTierEnum.HIGH, trend=TrendEnum.STABLE)
    db_session.add_all([s_base, s_post1])
    db_session.commit()

    i1 = Intervention(student_id=1, title="Action 1", created_at=t_interv)
    db_session.add(i1)
    db_session.commit()
    r1 = client.get(f"/api/interventions/{i1.id}/effectiveness").json()
    assert r1["classification"] == "IMPROVED"
    assert r1["score_delta"] == -5.0

    # Subtest 2: delta = -4.9 -> STABLE
    s_post1.final_score = 55.1
    db_session.commit()
    r2 = client.get(f"/api/interventions/{i1.id}/effectiveness").json()
    assert r2["classification"] == "STABLE"
    assert r2["score_delta"] == -4.9

    # Subtest 3: delta = +4.9 -> STABLE
    s_post1.final_score = 64.9
    db_session.commit()
    r3 = client.get(f"/api/interventions/{i1.id}/effectiveness").json()
    assert r3["classification"] == "STABLE"
    assert r3["score_delta"] == 4.9

    # Subtest 4: delta = +5.0 -> WORSENED
    s_post1.final_score = 65.0
    db_session.commit()
    r4 = client.get(f"/api/interventions/{i1.id}/effectiveness").json()
    assert r4["classification"] == "WORSENED"
    assert r4["score_delta"] == 5.0


def test_insufficient_data_and_awaiting_reassessment(client, db_session: Session):
    """Tests 9 & 10: Missing baseline returns INSUFFICIENT_DATA; missing post returns AWAITING_REASSESSMENT."""
    t_interv = datetime(2026, 8, 10, 12, 0, 0, tzinfo=timezone.utc)

    # Case A: No snapshots at all -> INSUFFICIENT_DATA
    i_no_data = Intervention(student_id=1, title="No Snapshot Student", created_at=t_interv)
    db_session.add(i_no_data)
    db_session.commit()
    r_no_data = client.get(f"/api/interventions/{i_no_data.id}/effectiveness").json()
    assert r_no_data["classification"] == "INSUFFICIENT_DATA"
    assert r_no_data["before"] is None
    assert r_no_data["after"] is None

    # Case B: Only baseline snapshot -> AWAITING_REASSESSMENT
    s_base = RiskSnapshot(
        student_id=1,
        computed_at=datetime(2026, 8, 5, 10, 0, 0, tzinfo=timezone.utc),
        rule_score=60.0,
        ml_probability=0.6,
        final_score=60.0,
        risk_tier=RiskTierEnum.HIGH,
        trend=TrendEnum.STABLE,
    )
    db_session.add(s_base)
    db_session.commit()

    r_awaiting = client.get(f"/api/interventions/{i_no_data.id}/effectiveness").json()
    assert r_awaiting["classification"] == "AWAITING_REASSESSMENT"
    assert r_awaiting["before"] is not None
    assert r_awaiting["after"] is None
    assert "A new student risk assessment is required" in r_awaiting["interpretation"]


def test_missing_intervention_returns_404(client):
    """Test 13: Missing intervention ID returns 404."""
    res = client.get("/api/interventions/999999/effectiveness")
    assert res.status_code == 404


def test_student_isolation_and_multiple_interventions(client, db_session: Session):
    """Tests 14 & 15: Student isolation and multiple interventions evaluation."""
    t1 = datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    t_int1 = datetime(2026, 8, 5, 12, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 10, 10, 0, 0, tzinfo=timezone.utc)
    t_int2 = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
    t3 = datetime(2026, 8, 20, 10, 0, 0, tzinfo=timezone.utc)

    # Student 1 snapshots
    s1_1 = RiskSnapshot(student_id=1, computed_at=t1, rule_score=80.0, ml_probability=0.8, final_score=80.0, risk_tier=RiskTierEnum.CRITICAL, trend=TrendEnum.STABLE)
    s1_2 = RiskSnapshot(student_id=1, computed_at=t2, rule_score=60.0, ml_probability=0.6, final_score=60.0, risk_tier=RiskTierEnum.HIGH, trend=TrendEnum.IMPROVING)
    s1_3 = RiskSnapshot(student_id=1, computed_at=t3, rule_score=40.0, ml_probability=0.4, final_score=40.0, risk_tier=RiskTierEnum.MEDIUM, trend=TrendEnum.IMPROVING)

    # Student 2 snapshot
    s2_1 = RiskSnapshot(student_id=2, computed_at=t1, rule_score=20.0, ml_probability=0.2, final_score=20.0, risk_tier=RiskTierEnum.LOW, trend=TrendEnum.STABLE)
    db_session.add_all([s1_1, s1_2, s1_3, s2_1])
    db_session.commit()

    i1 = Intervention(student_id=1, title="Interv 1", created_at=t_int1)
    i2 = Intervention(student_id=1, title="Interv 2", created_at=t_int2)
    db_session.add_all([i1, i2])
    db_session.commit()

    # i1: baseline is s1_1 (80.0), post is s1_3 (40.0) -> delta = -40.0
    r_i1 = client.get(f"/api/interventions/{i1.id}/effectiveness").json()
    assert r_i1["before"]["score"] == 80.0
    assert r_i1["after"]["score"] == 40.0
    assert r_i1["score_delta"] == -40.0

    # i2: baseline is s1_2 (60.0), post is s1_3 (40.0) -> delta = -20.0
    r_i2 = client.get(f"/api/interventions/{i2.id}/effectiveness").json()
    assert r_i2["before"]["score"] == 60.0
    assert r_i2["after"]["score"] == 40.0
    assert r_i2["score_delta"] == -20.0


def test_aggregate_effectiveness_summary(client, db_session: Session):
    """Tests 16, 17, 18, 19, 20: Aggregate summary metrics (improved, stable, worsened, awaiting, avg delta)."""
    t_before = datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    t_int = datetime(2026, 8, 5, 12, 0, 0, tzinfo=timezone.utc)
    t_after = datetime(2026, 8, 10, 10, 0, 0, tzinfo=timezone.utc)

    # Student 1: Improved (-20.0)
    s1_b = RiskSnapshot(student_id=1, computed_at=t_before, rule_score=70.0, ml_probability=0.7, final_score=70.0, risk_tier=RiskTierEnum.HIGH, trend=TrendEnum.STABLE)
    s1_a = RiskSnapshot(student_id=1, computed_at=t_after, rule_score=50.0, ml_probability=0.5, final_score=50.0, risk_tier=RiskTierEnum.MEDIUM, trend=TrendEnum.IMPROVING)

    # Student 2: Worsened (+10.0)
    s2_b = RiskSnapshot(student_id=2, computed_at=t_before, rule_score=30.0, ml_probability=0.3, final_score=30.0, risk_tier=RiskTierEnum.LOW, trend=TrendEnum.STABLE)
    s2_a = RiskSnapshot(student_id=2, computed_at=t_after, rule_score=40.0, ml_probability=0.4, final_score=40.0, risk_tier=RiskTierEnum.MEDIUM, trend=TrendEnum.GRADUALLY_DETERIORATING)

    db_session.add_all([s1_b, s1_a, s2_b, s2_a])
    db_session.commit()

    i1 = Intervention(student_id=1, title="Action 1", created_at=t_int)
    i2 = Intervention(student_id=2, title="Action 2", created_at=t_int)
    # Student 1 action 3: awaiting (created after t_after)
    i3 = Intervention(student_id=1, title="Action 3", created_at=datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc))
    db_session.add_all([i1, i2, i3])
    db_session.commit()

    res = client.get("/api/interventions/effectiveness/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_interventions"] == 3
    assert data["evaluated_interventions"] == 2
    assert data["improved_count"] == 1
    assert data["worsened_count"] == 1
    assert data["awaiting_reassessment_count"] == 1
    # Average delta = (-20.0 + 10.0) / 2 = -5.0
    assert data["average_score_change"] == -5.0


def test_follow_up_state_classification_and_api(client, db_session: Session):
    """Tests 21, 22, 23, 24, 25, 26, 27, 28: Follow-up urgency states and filtering."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    i_overdue = Intervention(student_id=1, title="Overdue Action", status="IN_PROGRESS", follow_up_date=yesterday)
    i_due_today = Intervention(student_id=1, title="Due Today Action", status="PLANNED", follow_up_date=today)
    i_upcoming = Intervention(student_id=1, title="Upcoming Action", status="PLANNED", follow_up_date=tomorrow)
    i_no_date = Intervention(student_id=1, title="No Date Action", status="PLANNED", follow_up_date=None)
    i_completed = Intervention(student_id=1, title="Closed Action", status="COMPLETED", follow_up_date=yesterday)
    i_cancelled = Intervention(student_id=1, title="Cancelled Action", status="CANCELLED", follow_up_date=yesterday)

    db_session.add_all([i_overdue, i_due_today, i_upcoming, i_no_date, i_completed, i_cancelled])
    db_session.commit()

    # Query all follow-ups
    res_all = client.get("/api/interventions/follow-ups")
    assert res_all.status_code == 200
    data = res_all.json()
    assert data["total"] == 6
    assert data["overdue_count"] == 1
    assert data["due_today_count"] == 1
    assert data["upcoming_count"] == 1

    # Filter by state=OVERDUE
    res_overdue = client.get("/api/interventions/follow-ups?state=OVERDUE")
    assert res_overdue.status_code == 200
    assert len(res_overdue.json()["items"]) == 1
    assert res_overdue.json()["items"][0]["title"] == "Overdue Action"
    assert res_overdue.json()["items"][0]["follow_up_state"] == "OVERDUE"

    # Filter by state=CLOSED
    res_closed = client.get("/api/interventions/follow-ups?state=CLOSED")
    assert res_closed.status_code == 200
    assert len(res_closed.json()["items"]) == 2


def test_effectiveness_and_followup_get_read_only(client, db_session: Session):
    """Tests 29 & 30: GET endpoints are strictly read-only and create zero records or notifications."""
    i = Intervention(student_id=1, title="Test Read Only", status="PLANNED")
    db_session.add(i)
    db_session.commit()
    db_session.refresh(i)

    cnt_interv_before = db_session.query(Intervention).count()
    cnt_notif_before = db_session.query(Notification).count()
    cnt_snap_before = db_session.query(RiskSnapshot).count()

    client.get(f"/api/interventions/{i.id}/effectiveness")
    client.get("/api/interventions/effectiveness/summary")
    client.get("/api/interventions/follow-ups")

    assert db_session.query(Intervention).count() == cnt_interv_before
    assert db_session.query(Notification).count() == cnt_notif_before
    assert db_session.query(RiskSnapshot).count() == cnt_snap_before
