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
from app.models.intervention import (
    Intervention,
    InterventionTypeEnum,
    InterventionStatusEnum,
)
from app.schemas.intervention import InterventionCreate, InterventionUpdate
from app.services.interventions import InterventionService


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

    mentor1 = Mentor(id=1, name="Dr. Alan Turing", email="turing@institute.edu", department="CSE")
    mentor2 = Mentor(id=2, name="Dr. Grace Hopper", email="hopper@institute.edu", department="ECE")
    session.add_all([mentor1, mentor2])
    session.commit()

    student1 = Student(
        id=1,
        roll_number="CS2026001",
        name="Alice Walker",
        department="CSE",
        semester=4,
        mentor_id=1,
    )
    student2 = Student(
        id=2,
        roll_number="EC2026002",
        name="Bob Martin",
        department="ECE",
        semester=3,
        mentor_id=2,
    )
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


def test_create_intervention_success(client, db_session: Session):
    """Test 1: Create intervention with valid student, mentor, type, and title."""
    payload = {
        "student_id": 1,
        "mentor_id": 1,
        "intervention_type": "COUNSELLING",
        "title": "Academic Counselling Session",
        "notes": "Met with student to discuss mid-term performance.",
        "status": "PLANNED",
        "follow_up_date": (date.today() + timedelta(days=7)).isoformat(),
    }
    response = client.post("/api/interventions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["student_id"] == 1
    assert data["student_name"] == "Alice Walker"
    assert data["mentor_id"] == 1
    assert data["mentor_name"] == "Dr. Alan Turing"
    assert data["intervention_type"] == "COUNSELLING"
    assert data["title"] == "Academic Counselling Session"
    assert data["status"] == "PLANNED"
    assert data["notes"] == "Met with student to discuss mid-term performance."
    assert data["completed_at"] is None


def test_create_intervention_invalid_student_returns_404(client):
    """Test 2: Creating intervention for nonexistent student returns 404."""
    payload = {
        "student_id": 99999,
        "title": "Test Title",
        "intervention_type": "ACADEMIC_SUPPORT",
    }
    response = client.post("/api/interventions", json=payload)
    assert response.status_code == 404
    assert "Student with ID 99999 not found" in response.json()["detail"]


def test_create_intervention_invalid_mentor_returns_404(client):
    """Test 3: Creating intervention with nonexistent mentor returns 404."""
    payload = {
        "student_id": 1,
        "mentor_id": 99999,
        "title": "Test Title",
        "intervention_type": "COUNSELLING",
    }
    response = client.post("/api/interventions", json=payload)
    assert response.status_code == 404
    assert "Mentor with ID 99999 not found" in response.json()["detail"]


def test_create_intervention_invalid_type_returns_422(client):
    """Test 4: Unknown intervention type is rejected with 422 validation error."""
    payload = {
        "student_id": 1,
        "title": "Test Title",
        "intervention_type": "INVALID_TYPE_ENUM",
    }
    response = client.post("/api/interventions", json=payload)
    assert response.status_code == 422


def test_create_intervention_invalid_status_returns_422(client):
    """Test 5: Unknown status string is rejected with 422 validation error."""
    payload = {
        "student_id": 1,
        "title": "Test Title",
        "status": "INVALID_STATUS_NAME",
    }
    response = client.post("/api/interventions", json=payload)
    assert response.status_code == 422


def test_create_intervention_empty_title_rejected(client):
    """Test 6: Empty or whitespace-only title is rejected."""
    payload = {
        "student_id": 1,
        "title": "   ",
        "intervention_type": "COUNSELLING",
    }
    response = client.post("/api/interventions", json=payload)
    assert response.status_code == 422


def test_retrieve_intervention_by_id(client, db_session: Session):
    """Test 7: Retrieve an existing intervention by ID."""
    notif = Intervention(
        student_id=1,
        mentor_id=1,
        intervention_type="ACADEMIC_SUPPORT",
        title="Peer Tutoring Assignment",
        notes="Assigned senior peer tutor for DSA.",
        status="IN_PROGRESS",
    )
    db_session.add(notif)
    db_session.commit()
    db_session.refresh(notif)

    response = client.get(f"/api/interventions/{notif.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == notif.id
    assert data["title"] == "Peer Tutoring Assignment"
    assert data["status"] == "IN_PROGRESS"


def test_retrieve_missing_intervention_returns_404(client):
    """Test 8: Retrieving missing intervention returns 404."""
    response = client.get("/api/interventions/88888")
    assert response.status_code == 404


def test_list_interventions_and_pagination(client, db_session: Session):
    """Tests 9 & 10: List interventions with pagination."""
    for i in range(15):
        db_session.add(
            Intervention(
                student_id=1,
                mentor_id=1,
                intervention_type="COUNSELLING",
                title=f"Session {i}",
                status="PLANNED",
            )
        )
    db_session.commit()

    response = client.get("/api/interventions?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert data["total"] == 15
    assert data["pages"] == 3


def test_interventions_filtering(client, db_session: Session):
    """Tests 11, 12, 13, 14: Filter by student, status, type, and mentor."""
    i1 = Intervention(
        student_id=1,
        mentor_id=1,
        intervention_type="COUNSELLING",
        title="Student 1 Counselling",
        status="PLANNED",
    )
    i2 = Intervention(
        student_id=2,
        mentor_id=2,
        intervention_type="FINANCIAL_GUIDANCE",
        title="Student 2 Fee Guidance",
        status="COMPLETED",
    )
    db_session.add_all([i1, i2])
    db_session.commit()

    # Filter by student_id
    res_student = client.get("/api/interventions?student_id=1")
    assert res_student.status_code == 200
    assert len(res_student.json()["items"]) == 1
    assert res_student.json()["items"][0]["student_id"] == 1

    # Filter by status
    res_status = client.get("/api/interventions?status=COMPLETED")
    assert res_status.status_code == 200
    assert len(res_status.json()["items"]) == 1
    assert res_status.json()["items"][0]["status"] == "COMPLETED"

    # Filter by type
    res_type = client.get("/api/interventions?intervention_type=FINANCIAL_GUIDANCE")
    assert res_type.status_code == 200
    assert len(res_type.json()["items"]) == 1
    assert res_type.json()["items"][0]["intervention_type"] == "FINANCIAL_GUIDANCE"

    # Filter by mentor
    res_mentor = client.get("/api/interventions?mentor_id=2")
    assert res_mentor.status_code == 200
    assert len(res_mentor.json()["items"]) == 1
    assert res_mentor.json()["items"][0]["mentor_id"] == 2


def test_newest_first_ordering(client, db_session: Session):
    """Test 15: Interventions returned newest first."""
    i_old = Intervention(
        student_id=1,
        title="Old Session",
        intervention_type="COUNSELLING",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    i_new = Intervention(
        student_id=1,
        title="New Session",
        intervention_type="COUNSELLING",
        created_at=datetime(2026, 8, 20, tzinfo=timezone.utc),
    )
    db_session.add_all([i_old, i_new])
    db_session.commit()

    res = client.get("/api/interventions?student_id=1")
    items = res.json()["items"]
    assert items[0]["title"] == "New Session"
    assert items[1]["title"] == "Old Session"


def test_update_intervention_title_notes_and_follow_up(client, db_session: Session):
    """Tests 16, 17, 18: Update title, notes, and follow-up date."""
    i = Intervention(
        student_id=1,
        mentor_id=1,
        title="Initial Title",
        notes="Initial notes.",
        intervention_type="COUNSELLING",
        status="PLANNED",
    )
    db_session.add(i)
    db_session.commit()
    db_session.refresh(i)

    new_date = (date.today() + timedelta(days=14)).isoformat()
    patch_res = client.patch(
        f"/api/interventions/{i.id}",
        json={
            "title": "Updated Session Title",
            "notes": "Updated notes with detailed progress.",
            "follow_up_date": new_date,
        },
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["title"] == "Updated Session Title"
    assert data["notes"] == "Updated notes with detailed progress."
    assert data["follow_up_date"] == new_date


def test_status_lifecycle_and_completed_at(client, db_session: Session):
    """Tests 19, 20, 21, 22: Lifecycle transitions and completed_at behavior."""
    i = Intervention(
        student_id=1,
        mentor_id=1,
        title="Support Lifecycle",
        intervention_type="ATTENDANCE_SUPPORT",
        status="PLANNED",
    )
    db_session.add(i)
    db_session.commit()
    db_session.refresh(i)
    assert i.completed_at is None

    # Transition: PLANNED -> IN_PROGRESS
    res_in_prog = client.patch(f"/api/interventions/{i.id}", json={"status": "IN_PROGRESS"})
    assert res_in_prog.status_code == 200
    assert res_in_prog.json()["status"] == "IN_PROGRESS"
    assert res_in_prog.json()["completed_at"] is None

    # Transition: IN_PROGRESS -> COMPLETED
    res_completed = client.patch(f"/api/interventions/{i.id}", json={"status": "COMPLETED"})
    assert res_completed.status_code == 200
    assert res_completed.json()["status"] == "COMPLETED"
    assert res_completed.json()["completed_at"] is not None

    # Reopening: COMPLETED -> IN_PROGRESS clears completed_at
    res_reopened = client.patch(f"/api/interventions/{i.id}", json={"status": "IN_PROGRESS"})
    assert res_reopened.status_code == 200
    assert res_reopened.json()["status"] == "IN_PROGRESS"
    assert res_reopened.json()["completed_at"] is None

    # Cancellation: IN_PROGRESS -> CANCELLED
    res_cancelled = client.patch(f"/api/interventions/{i.id}", json={"status": "CANCELLED"})
    assert res_cancelled.status_code == 200
    assert res_cancelled.json()["status"] == "CANCELLED"


def test_student_intervention_history_isolation(client, db_session: Session):
    """Tests 23 & 24: Student history isolation ensures no unrelated records are returned."""
    i_s1 = Intervention(student_id=1, title="S1 Plan", intervention_type="COUNSELLING")
    i_s2 = Intervention(student_id=2, title="S2 Plan", intervention_type="COUNSELLING")
    db_session.add_all([i_s1, i_s2])
    db_session.commit()

    res1 = client.get("/api/interventions?student_id=1")
    items1 = res1.json()["items"]
    assert len(items1) == 1
    assert items1[0]["title"] == "S1 Plan"
    assert all(item["student_id"] == 1 for item in items1)

    res2 = client.get("/api/interventions?student_id=2")
    items2 = res2.json()["items"]
    assert len(items2) == 1
    assert items2[0]["title"] == "S2 Plan"
    assert all(item["student_id"] == 2 for item in items2)


def test_interventions_summary_and_follow_up_due(client, db_session: Session):
    """Tests 25 & 26: Summary endpoint and follow-up due calculations."""
    yesterday = date.today() - timedelta(days=1)
    future = date.today() + timedelta(days=5)

    i1 = Intervention(
        student_id=1,
        title="Due Action",
        status="IN_PROGRESS",
        follow_up_date=yesterday,
    )
    i2 = Intervention(
        student_id=1,
        title="Future Action",
        status="PLANNED",
        follow_up_date=future,
    )
    i3 = Intervention(
        student_id=2,
        title="Completed Past Action",
        status="COMPLETED",
        follow_up_date=yesterday,
    )
    db_session.add_all([i1, i2, i3])
    db_session.commit()

    res = client.get("/api/interventions/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_interventions"] == 3
    assert data["active_count"] == 1
    assert data["planned_count"] == 1
    assert data["completed_count"] == 1
    # Only i1 has follow_up_date <= today and is NOT completed/cancelled
    assert data["follow_ups_due_count"] == 1

    # Filter follow_ups_due
    res_due = client.get("/api/interventions?follow_ups_due=true")
    assert res_due.status_code == 200
    assert len(res_due.json()["items"]) == 1
    assert res_due.json()["items"][0]["title"] == "Due Action"
    assert res_due.json()["items"][0]["is_follow_up_due"] is True
