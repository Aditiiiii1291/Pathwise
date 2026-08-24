import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

try:
    from app.core.database import Base, get_db
    from app.models import Student, AttendanceRecord, MarksRecord, FeeRecord, RiskSnapshot
    from app.main import app
except ImportError:
    from backend.app.core.database import Base, get_db
    from backend.app.models import Student, AttendanceRecord, MarksRecord, FeeRecord, RiskSnapshot
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

    # Seed student with attendance and marks
    s1 = Student(
        id=1,
        roll_number="2026CSE001",
        name="Ada Lovelace",
        department="CSE",
        semester=4,
    )
    session.add(s1)

    # 4 weeks attendance
    for w in range(1, 5):
        session.add(
            AttendanceRecord(
                student_id=1,
                week_number=w,
                month="August",
                total_classes=20,
                attended_classes=12 if w > 2 else 18,
                percentage=60.0 if w > 2 else 90.0,
            )
        )

    # 2 exam marks
    session.add(
        MarksRecord(
            student_id=1,
            subject_name="Data Structures",
            exam_type="MIDTERM",
            max_marks=100.0,
            obtained_marks=45.0,
            attempt_number=1,
        )
    )
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

def test_assessment_get_read_only(client, db_session):
    """Verify GET /api/students/{id}/assessment computes on-demand without persisting snapshot."""
    initial_count = db_session.query(RiskSnapshot).count()
    res = client.get("/api/students/1/assessment")
    assert res.status_code == 200
    data = res.json()

    assert data["student_id"] == 1
    assert "assessment" in data
    assert "explanation" in data
    assert 0.0 <= data["assessment"]["final_score"] <= 100.0
    assert data["assessment"]["risk_tier"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert data["assessment"]["trend"] in ("RAPIDLY_DETERIORATING", "GRADUALLY_DETERIORATING", "STABLE", "IMPROVING")

    # Snapshot count should remain unchanged for GET
    after_count = db_session.query(RiskSnapshot).count()
    assert after_count == initial_count

def test_assessment_post_persists_snapshot_append_only(client, db_session):
    """Verify POST /api/students/{id}/assessment creates persistent snapshots in append-only fashion."""
    assert db_session.query(RiskSnapshot).count() == 0

    # First POST -> snapshot count = 1
    res1 = client.post("/api/students/1/assessment")
    assert res1.status_code == 200
    assert db_session.query(RiskSnapshot).count() == 1
    snap1 = db_session.query(RiskSnapshot).first()

    # Second POST -> snapshot count = 2
    res2 = client.post("/api/students/1/assessment")
    assert res2.status_code == 200
    assert db_session.query(RiskSnapshot).count() == 2

    # Snapshots should be distinct records
    snaps = db_session.query(RiskSnapshot).all()
    assert snaps[0].id != snaps[1].id
    assert snaps[0].student_id == snaps[1].student_id == 1

def test_assessment_response_structure_and_no_leakage(client):
    """Verify clean response schema without fake local attribution or forbidden keywords."""
    res = client.get("/api/students/1/assessment")
    assert res.status_code == 200
    data = res.json()

    # Integrity checks
    assert "model_confidence" not in data["assessment"]
    assert "will_dropout" not in data["assessment"]
    assert "dropout_label" not in data
    assert "trajectory_type" not in data

    # Explanation integrity
    explanation = data["explanation"]
    assert len(explanation["summary"]) > 0
    assert "global_ml_context" in explanation
    assert "top_global_features" in explanation["global_ml_context"]

def test_assessment_not_found(client):
    """Verify assessment on non-existent student returns 404."""
    res = client.get("/api/students/9999/assessment")
    assert res.status_code == 404
    assert res.status_code != 444
