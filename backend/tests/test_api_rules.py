import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

try:
    from app.core.database import Base, get_db
    from app.models import Student, RiskSnapshot, RuleConfig, RiskTierEnum, TrendEnum
    from app.main import app
except ImportError:
    from backend.app.core.database import Base, get_db
    from backend.app.models import Student, RiskSnapshot, RuleConfig, RiskTierEnum, TrendEnum
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

    # Seed an existing historical snapshot
    snap = RiskSnapshot(
        student_id=1,
        rule_score=65.0,
        ml_probability=0.70,
        final_score=67.5,
        risk_tier=RiskTierEnum.HIGH,
        trend=TrendEnum.GRADUALLY_DETERIORATING,
        factors_json={"attendance": 25.0},
    )
    session.add(snap)
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

def test_get_rules_default(client):
    """Verify GET /api/rules returns default balanced rule weights."""
    res = client.get("/api/rules")
    assert res.status_code == 200
    data = res.json()
    assert data["weights"]["attendance"] == 0.30
    assert data["weights"]["marks"] == 0.25
    assert data["weights"]["backlogs"] == 0.15
    assert data["weights"]["fees"] == 0.10
    assert data["weights"]["trends"] == 0.20

def test_update_rules_valid(client, db_session):
    """Verify PUT /api/rules persists valid custom weights."""
    payload = {
        "department": "CSE",
        "weights": {
            "attendance": 0.40,
            "marks": 0.30,
            "backlogs": 0.20,
            "fees": 0.05,
            "trends": 0.05,
        },
        "thresholds": {
            "attendance_min": 70.0,
            "attendance_decline_max": 12.0,
            "attendance_slope_min": -4.0,
            "attendance_consecutive_decline_max": 3,
            "marks_min": 45.0,
            "marks_decline_max": 15.0,
            "marks_slope_min": -4.0,
            "consecutive_failures_max": 2,
            "failed_subjects_max": 1,
            "active_backlogs_max": 2,
            "fee_overdue_terms_max": 1,
        },
    }
    res = client.put("/api/rules", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["department"] == "CSE"
    assert data["weights"]["attendance"] == 0.40

    # Verify persisted in database
    get_res = client.get("/api/rules?department=CSE")
    assert get_res.status_code == 200
    assert get_res.json()["weights"]["attendance"] == 0.40

def test_update_rules_invalid_weights_rejected(client):
    """Verify PUT /api/rules rejects weights that do not sum to 1.0."""
    payload = {
        "department": "ECE",
        "weights": {
            "attendance": 0.50,
            "marks": 0.50,
            "backlogs": 0.20,  # Sum = 1.20
            "fees": 0.05,
            "trends": 0.05,
        },
        "thresholds": {},
    }
    res = client.put("/api/rules", json=payload)
    assert res.status_code == 422

def test_update_rules_preserves_historical_snapshots(client, db_session):
    """Verify updating rule configurations does not rewrite historical RiskSnapshots."""
    initial_snap = db_session.query(RiskSnapshot).first()
    initial_score = initial_snap.final_score

    payload = {
        "department": None,
        "weights": {
            "attendance": 0.50,
            "marks": 0.20,
            "backlogs": 0.20,
            "fees": 0.05,
            "trends": 0.05,
        },
        "thresholds": {},
    }
    res = client.put("/api/rules", json=payload)
    assert res.status_code == 200

    # Historical snapshot should be strictly untouched
    reloaded_snap = db_session.query(RiskSnapshot).first()
    assert reloaded_snap.final_score == initial_score
    assert reloaded_snap.rule_score == 65.0
