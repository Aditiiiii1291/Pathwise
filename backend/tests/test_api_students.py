import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

try:
    from app.core.database import Base, get_db
    from app.models import Student, Mentor, RiskSnapshot, RiskTierEnum, TrendEnum
    from app.main import app
except ImportError:
    from backend.app.core.database import Base, get_db
    from backend.app.models import Student, Mentor, RiskSnapshot, RiskTierEnum, TrendEnum
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

    # Seed mentors and students
    m1 = Mentor(id=1, name="Dr. Alan Turing", email="turing@institute.edu", department="CSE")
    session.add(m1)

    for i in range(1, 26):
        dept = "CSE" if i % 2 == 0 else "ECE"
        s = Student(
            id=i,
            roll_number=f"2026{dept}{i:03d}",
            name=f"Student {i}",
            department=dept,
            semester=4 if i % 2 == 0 else 6,
            guardian_name=f"Guardian {i}",
            guardian_phone="+919876543210",
            guardian_email=f"guardian{i}@example.com",
            enrollment_year=2024,
            mentor_id=1,
        )
        session.add(s)

    # Add snapshot for student 1 & 2
    snap1 = RiskSnapshot(
        student_id=1,
        rule_score=80.0,
        ml_probability=0.85,
        final_score=82.5,
        risk_tier=RiskTierEnum.CRITICAL,
        trend=TrendEnum.RAPIDLY_DETERIORATING,
        factors_json={"attendance": 30.0},
    )
    snap2 = RiskSnapshot(
        student_id=2,
        rule_score=10.0,
        ml_probability=0.10,
        final_score=10.0,
        risk_tier=RiskTierEnum.LOW,
        trend=TrendEnum.STABLE,
        factors_json={},
    )
    session.add_all([snap1, snap2])
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

def test_student_list_pagination(client):
    """Verify student list pagination and default page size."""
    res = client.get("/api/students?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total"] == 25
    assert data["pages"] == 3
    assert len(data["items"]) == 10

def test_student_list_page_size_limit(client):
    """Verify page_size cannot exceed 100 or be less than 1."""
    res_high = client.get("/api/students?page_size=150")
    assert res_high.status_code == 422

    res_zero = client.get("/api/students?page_size=0")
    assert res_zero.status_code == 422

def test_student_list_search_and_filters(client):
    """Verify search, department, semester, risk_tier, and trend filters."""
    # Search by roll number
    res = client.get("/api/students?search=2026CSE002")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["roll_number"] == "2026CSE002"

    # Search by name
    res = client.get("/api/students?search=Student 5")
    assert res.status_code == 200
    assert res.json()["total"] == 1

    # Department filter
    res = client.get("/api/students?department=CSE")
    assert res.status_code == 200
    assert res.json()["total"] == 12

    # Semester filter
    res = client.get("/api/students?semester=6")
    assert res.status_code == 200
    assert res.json()["total"] == 13

    # Risk tier filter
    res = client.get("/api/students?risk_tier=CRITICAL")
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["id"] == 1

    # Trend filter
    res = client.get("/api/students?trend=RAPIDLY_DETERIORATING")
    assert res.status_code == 200
    assert res.json()["total"] == 1

def test_student_list_privacy_no_guardian_contact(client):
    """Verify student list items do NOT expose guardian email/phone."""
    res = client.get("/api/students?page=1&page_size=5")
    assert res.status_code == 200
    items = res.json()["items"]
    for item in items:
        assert "guardian_phone" not in item
        assert "guardian_email" not in item

def test_student_profile_success(client):
    """Verify GET /api/students/{id} returns full unified profile."""
    res = client.get("/api/students/1")
    assert res.status_code == 200
    data = res.json()
    assert data["profile"]["student"]["id"] == 1
    assert data["profile"]["student"]["name"] == "Student 1"
    assert data["latest_assessment"] is not None
    assert data["latest_assessment"]["risk_tier"] == "CRITICAL"

def test_student_profile_not_found(client):
    """Verify GET /api/students/{id} with missing student returns 404 (NOT 444)."""
    res = client.get("/api/students/9999")
    assert res.status_code == 404
    assert res.status_code != 444
