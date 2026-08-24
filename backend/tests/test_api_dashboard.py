import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

try:
    from app.core.database import Base, get_db
    from app.models import Student, RiskSnapshot, RiskTierEnum, TrendEnum
    from app.main import app
except ImportError:
    from backend.app.core.database import Base, get_db
    from backend.app.models import Student, RiskSnapshot, RiskTierEnum, TrendEnum
    from backend.app.main import app

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

    # Create 3 students
    s1 = Student(id=1, roll_number="CSE001", name="Student 1", department="CSE", semester=4)
    s2 = Student(id=2, roll_number="CSE002", name="Student 2", department="CSE", semester=4)
    s3 = Student(id=3, roll_number="ECE001", name="Student 3", department="ECE", semester=6)
    session.add_all([s1, s2, s3])
    session.commit()

    # Historical snapshot for Student 1 (old)
    snap1_old = RiskSnapshot(
        student_id=1,
        rule_score=30.0,
        ml_probability=0.30,
        final_score=30.0,
        risk_tier=RiskTierEnum.MEDIUM,
        trend=TrendEnum.STABLE,
        factors_json={},
    )
    # Latest snapshot for Student 1 (new)
    snap1_new = RiskSnapshot(
        student_id=1,
        rule_score=80.0,
        ml_probability=0.80,
        final_score=80.0,
        risk_tier=RiskTierEnum.CRITICAL,
        trend=TrendEnum.RAPIDLY_DETERIORATING,
        factors_json={},
    )
    # Latest snapshot for Student 2
    snap2 = RiskSnapshot(
        student_id=2,
        rule_score=10.0,
        ml_probability=0.10,
        final_score=10.0,
        risk_tier=RiskTierEnum.LOW,
        trend=TrendEnum.IMPROVING,
        factors_json={},
    )
    session.add_all([snap1_old, snap1_new, snap2])
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
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()

def test_dashboard_overview_metrics_and_no_double_counting(client):
    """Verify overview uses only the latest snapshot per student and counts accurately."""
    res = client.get("/api/dashboard/overview")
    assert res.status_code == 200
    data = res.json()

    assert data["total_students"] == 3
    assert data["assessed_students"] == 2

    # Risk distribution: 1 LOW (student 2), 0 MEDIUM, 0 HIGH, 1 CRITICAL (student 1 latest)
    assert data["risk_distribution"]["LOW"] == 1
    assert data["risk_distribution"]["MEDIUM"] == 0  # old snap1_old is NOT double counted!
    assert data["risk_distribution"]["HIGH"] == 0
    assert data["risk_distribution"]["CRITICAL"] == 1

    # Trend distribution
    assert data["trend_distribution"]["IMPROVING"] == 1
    assert data["trend_distribution"]["RAPIDLY_DETERIORATING"] == 1

    # Average score: (80.0 + 10.0) / 2 = 45.0
    assert data["average_final_score"] == 45.0

def test_dashboard_departments_breakdown(client):
    """Verify department aggregation endpoint."""
    res = client.get("/api/dashboard/departments")
    assert res.status_code == 200
    data = res.json()

    assert len(data) == 2
    dept_names = {d["department"] for d in data}
    assert dept_names == {"CSE", "ECE"}

    cse = next(d for d in data if d["department"] == "CSE")
    assert cse["student_count"] == 2
    assert cse["at_risk_count"] == 1
    assert cse["critical_count"] == 1

    ece = next(d for d in data if d["department"] == "ECE")
    assert ece["student_count"] == 1
    assert ece["at_risk_count"] == 0

def test_historical_snapshots_state_transition(client, db_session):
    """
    Verify that when a student transitions from older CRITICAL to newer LOW,
    the dashboard overview reflects LOW / IMPROVING and not CRITICAL.
    """
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)

    # Student 4
    s4 = Student(id=4, roll_number="CSE004", name="Student 4", department="CSE", semester=2)
    db_session.add(s4)

    # Older snapshot: CRITICAL, RAPIDLY_DETERIORATING
    snap_old = RiskSnapshot(
        student_id=4,
        rule_score=85.0,
        ml_probability=0.90,
        final_score=87.5,
        risk_tier=RiskTierEnum.CRITICAL,
        trend=TrendEnum.RAPIDLY_DETERIORATING,
        computed_at=now - timedelta(days=30),
        factors_json={},
    )
    # Newer snapshot: LOW, IMPROVING
    snap_new = RiskSnapshot(
        student_id=4,
        rule_score=15.0,
        ml_probability=0.10,
        final_score=12.5,
        risk_tier=RiskTierEnum.LOW,
        trend=TrendEnum.IMPROVING,
        computed_at=now,
        factors_json={},
    )
    db_session.add_all([snap_old, snap_new])
    db_session.commit()

    res = client.get("/api/dashboard/overview")
    assert res.status_code == 200
    data = res.json()

    # Total assessed = 3 (student 1, student 2, student 4)
    assert data["assessed_students"] == 3
    # Student 4 must be counted as LOW (total LOW = student 2 + student 4 = 2)
    assert data["risk_distribution"]["LOW"] == 2
    # Student 4 is NOT counted as CRITICAL (only student 1 is CRITICAL)
    assert data["risk_distribution"]["CRITICAL"] == 1
    # Student 4 must be counted as IMPROVING (total IMPROVING = student 2 + student 4 = 2)
    assert data["trend_distribution"]["IMPROVING"] == 2

def test_computed_at_determines_latest_state_inverted_id(client, db_session):
    """
    Verify that computed_at determines latest state even when insertion ID order is inverted
    (e.g., an older record inserted with a higher ID).
    """
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)

    # Student 5
    s5 = Student(id=5, roll_number="ECE005", name="Student 5", department="ECE", semester=2)
    db_session.add(s5)
    db_session.commit()

    # Insert newer snapshot first (will get smaller ID)
    snap_newer = RiskSnapshot(
        student_id=5,
        rule_score=20.0,
        ml_probability=0.15,
        final_score=17.5,
        risk_tier=RiskTierEnum.LOW,
        trend=TrendEnum.IMPROVING,
        computed_at=now,
        factors_json={},
    )
    db_session.add(snap_newer)
    db_session.commit()

    # Insert older snapshot second (will get larger ID, but older computed_at)
    snap_older = RiskSnapshot(
        student_id=5,
        rule_score=90.0,
        ml_probability=0.95,
        final_score=92.5,
        risk_tier=RiskTierEnum.CRITICAL,
        trend=TrendEnum.RAPIDLY_DETERIORATING,
        computed_at=now - timedelta(days=60),
        factors_json={},
    )
    db_session.add(snap_older)
    db_session.commit()

    assert snap_older.id > snap_newer.id
    assert snap_newer.computed_at > snap_older.computed_at

    # Check student list filter: student 5 must be matched by LOW, not CRITICAL
    res_low = client.get("/api/students?risk_tier=LOW&search=Student 5")
    assert res_low.status_code == 200
    assert res_low.json()["total"] == 1

    res_crit = client.get("/api/students?risk_tier=CRITICAL&search=Student 5")
    assert res_crit.status_code == 200
    assert res_crit.json()["total"] == 0

    # Check trend filter: student 5 must be matched by IMPROVING, not RAPIDLY_DETERIORATING
    res_imp = client.get("/api/students?trend=IMPROVING&search=Student 5")
    assert res_imp.status_code == 200
    assert res_imp.json()["total"] == 1

    res_det = client.get("/api/students?trend=RAPIDLY_DETERIORATING&search=Student 5")
    assert res_det.status_code == 200
    assert res_det.json()["total"] == 0
