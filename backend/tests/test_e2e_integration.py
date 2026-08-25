import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User, UserRoleEnum
from app.models.mentor import Mentor
from app.models.student import Student
from app.models.risk import RiskSnapshot, RiskTierEnum, TrendEnum
from app.models.intervention import Intervention, InterventionTypeEnum, InterventionStatusEnum
from app.services.auth import AuthService
from app.schemas.auth import UserCreate


@pytest.fixture(scope="function")
def e2e_db():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()

    # 1. Seed Mentor
    mentor = Mentor(id=1, name="Dr. Grace Hopper", email="hopper@institute.edu", department="CSE")
    session.add(mentor)
    session.commit()

    # 2. Seed Students
    s1 = Student(id=1, roll_number="CS2026001", name="Alice Smith", department="CSE", semester=4, mentor_id=1)
    s2 = Student(id=2, roll_number="CS2026002", name="Bob Jones", department="CSE", semester=4, mentor_id=1)
    session.add_all([s1, s2])
    session.commit()

    # 3. Seed Risk Snapshots
    snap1 = RiskSnapshot(
        student_id=1,
        rule_score=65.0,
        ml_probability=0.72,
        final_score=68.5,
        risk_tier=RiskTierEnum.HIGH,
        trend=TrendEnum.GRADUALLY_DETERIORATING,
        factors_json={"attendance": {"score": 70.0}},
    )
    snap2 = RiskSnapshot(
        student_id=2,
        rule_score=15.0,
        ml_probability=0.10,
        final_score=12.5,
        risk_tier=RiskTierEnum.LOW,
        trend=TrendEnum.STABLE,
        factors_json={"attendance": {"score": 10.0}},
    )
    session.add_all([snap1, snap2])
    session.commit()

    # 4. Seed Staff Accounts
    AuthService.create_user(
        session,
        UserCreate(username="admin_user", password="Password123", display_name="System Admin", role=UserRoleEnum.ADMIN.value),
    )
    AuthService.create_user(
        session,
        UserCreate(username="mentor_user", password="Password123", display_name="Faculty Mentor", role=UserRoleEnum.MENTOR.value, mentor_id=1),
    )
    AuthService.create_user(
        session,
        UserCreate(username="counsellor_user", password="Password123", display_name="Student Counsellor", role=UserRoleEnum.COUNSELLOR.value),
    )

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(e2e_db):
    def override_get_db():
        try:
            yield e2e_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_complete_admin_end_to_end_flow(client):
    """E2E Test: Admin login -> overview -> roster -> profile -> rules -> upload -> logout."""
    # 1. Login
    res_login = client.post("/api/auth/login", json={"username": "admin_user", "password": "Password123"})
    assert res_login.status_code == 200
    admin_token = res_login.json()["access_token"]
    admin_refresh = res_login.json()["refresh_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Session verify
    res_me = client.get("/api/auth/me", headers=headers)
    assert res_me.status_code == 200
    assert res_me.json()["role"] == "ADMIN"

    # 3. Overview metrics
    res_ov = client.get("/api/dashboard/overview", headers=headers)
    assert res_ov.status_code == 200
    assert res_ov.json()["total_students"] == 2
    assert res_ov.json()["assessed_students"] == 2
    assert res_ov.json()["risk_distribution"]["HIGH"] == 1
    assert res_ov.json()["risk_distribution"]["LOW"] == 1

    # 4. Department metrics
    res_dept = client.get("/api/dashboard/departments", headers=headers)
    assert res_dept.status_code == 200
    assert len(res_dept.json()) >= 1
    assert res_dept.json()[0]["department"] == "CSE"

    # 5. Student Roster
    res_roster = client.get("/api/students", headers=headers)
    assert res_roster.status_code == 200
    assert res_roster.json()["total"] == 2
    assert res_roster.json()["items"][0]["roll_number"] == "CS2026001"

    # 6. Student Profile
    res_prof = client.get("/api/students/1", headers=headers)
    assert res_prof.status_code == 200
    assert res_prof.json()["profile"]["student"]["name"] == "Alice Smith"
    assert res_prof.json()["latest_assessment"]["risk_tier"] == "HIGH"

    # 7. Rules Update (Admin allowed)
    res_rules = client.put(
        "/api/rules",
        headers=headers,
        json={"weights": {"attendance": 0.35, "marks": 0.25, "backlogs": 0.2, "fees": 0.1, "trends": 0.1}, "thresholds": {}},
    )
    assert res_rules.status_code == 200

    # 8. Upload Dataset (Admin allowed)
    csv_data = "student_id,roll_number,name,department,semester\n3,CS2026003,Charlie,CSE,4\n"
    res_upload = client.post(
        "/api/uploads/students",
        headers=headers,
        files={"file": ("roster.csv", csv_data.encode("utf-8"), "text/csv")},
    )
    assert res_upload.status_code == 200
    assert res_upload.json()["valid_rows"] == 1

    # 9. Logout
    res_logout = client.post("/api/auth/logout", json={"refresh_token": admin_refresh})
    assert res_logout.status_code == 200


def test_complete_mentor_end_to_end_flow(client):
    """E2E Test: Mentor login -> roster -> profile -> intervention attribution -> RBAC limits."""
    # 1. Login
    res_login = client.post("/api/auth/login", json={"username": "mentor_user", "password": "Password123"})
    assert res_login.status_code == 200
    mentor_token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {mentor_token}"}

    # 2. View Profile
    res_prof = client.get("/api/students/1", headers=headers)
    assert res_prof.status_code == 200

    # 3. Create Intervention with spoofed mentor_id
    res_interv = client.post(
        "/api/interventions",
        headers=headers,
        json={
            "student_id": 1,
            "title": "Academic Tutoring Plan",
            "intervention_type": "ACADEMIC_SUPPORT",
            "status": "PLANNED",
            "mentor_id": 999,  # Attempted spoof
        },
    )
    assert res_interv.status_code == 201
    # Backend forces authenticated mentor_id
    assert res_interv.json()["mentor_id"] == 1

    # 4. View Intervention in List
    res_list = client.get("/api/interventions?student_id=1", headers=headers)
    assert res_list.status_code == 200
    assert res_list.json()["total"] == 1
    assert res_list.json()["items"][0]["title"] == "Academic Tutoring Plan"

    # 5. RBAC Forbidden Actions
    # Mentor cannot modify rules
    res_rules = client.put(
        "/api/rules",
        headers=headers,
        json={"weights": {"attendance": 0.4, "marks": 0.3, "backlogs": 0.2, "fees": 0.05, "trends": 0.05}, "thresholds": {}},
    )
    assert res_rules.status_code == 403

    # Mentor cannot upload datasets
    res_upload = client.post(
        "/api/uploads/students",
        headers=headers,
        files={"file": ("test.csv", b"student_id,name\n1,Test", "text/csv")},
    )
    assert res_upload.status_code == 403


def test_complete_counsellor_end_to_end_flow(client):
    """E2E Test: Counsellor login -> view interventions -> create counselling record -> RBAC limits."""
    # 1. Login
    res_login = client.post("/api/auth/login", json={"username": "counsellor_user", "password": "Password123"})
    assert res_login.status_code == 200
    counsellor_token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {counsellor_token}"}

    # 2. Create Counselling Intervention (no mentor_id required)
    res_interv = client.post(
        "/api/interventions",
        headers=headers,
        json={
            "student_id": 1,
            "title": "Stress & Workload Counselling",
            "intervention_type": "COUNSELLING",
            "status": "IN_PROGRESS",
            "notes": "Student discussed examination anxiety.",
        },
    )
    assert res_interv.status_code == 201
    assert res_interv.json()["mentor_id"] is None

    # 3. RBAC Forbidden Actions
    res_rules = client.put(
        "/api/rules",
        headers=headers,
        json={"weights": {"attendance": 0.4, "marks": 0.3, "backlogs": 0.2, "fees": 0.05, "trends": 0.05}, "thresholds": {}},
    )
    assert res_rules.status_code == 403


def test_cross_page_data_consistency(client):
    """E2E Test: Verify risk score, tier, and trend match across dashboard, roster, and profile."""
    res_login = client.post("/api/auth/login", json={"username": "admin_user", "password": "Password123"})
    headers = {"Authorization": f"Bearer {res_login.json()['access_token']}"}

    # Roster view
    res_roster = client.get("/api/students", headers=headers)
    student1_roster = [s for s in res_roster.json()["items"] if s["id"] == 1][0]

    # Profile view
    res_profile = client.get("/api/students/1", headers=headers)
    student1_profile = res_profile.json()["latest_assessment"]

    # Cross-page assertions
    assert student1_roster["latest_final_score"] == student1_profile["final_score"] == 68.5
    assert student1_roster["latest_risk_tier"] == student1_profile["risk_tier"] == "HIGH"
    assert student1_roster["latest_trend"] == student1_profile["trend"] == "GRADUALLY_DETERIORATING"
