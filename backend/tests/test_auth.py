import os
import pytest
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User, UserRoleEnum
from app.models.mentor import Mentor
from app.models.student import Student
from app.models.refresh_token import RefreshToken
from app.models.intervention import Intervention
from app.schemas.auth import UserCreate
from app.services.auth import AuthService
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_jwt_secret_key,
    JWT_ALGORITHM,
    verify_password,
    hash_refresh_token,
)


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

    # Seed mentor and student
    mentor = Mentor(id=1, name="Dr. Grace Hopper", email="hopper@institute.edu", department="CSE")
    session.add(mentor)
    session.commit()

    student = Student(id=1, roll_number="CS2026001", name="Alice Smith", department="CSE", semester=4, mentor_id=1)
    session.add(student)
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


def test_username_and_password_validation_rules(db_session: Session):
    """Tests: Username policies, case normalization, and password requirements."""
    # 1. Too short username (<3)
    with pytest.raises(Exception) as exc1:
        AuthService.create_user(db_session, UserCreate(username="ad", password="Password123", display_name="Ad"))
    assert "at least 3 characters" in str(exc1.value)

    # 2. Invalid characters in username
    with pytest.raises(Exception) as exc2:
        AuthService.create_user(db_session, UserCreate(username="user@name!", password="Password123", display_name="User"))
    assert "letters, numbers" in str(exc2.value)

    # 3. Password < 8 characters
    with pytest.raises(Exception) as exc3:
        AuthService.create_user(db_session, UserCreate(username="validuser", password="Pass1", display_name="User"))
    assert "at least 8 characters" in str(exc3.value)

    # 4. Password missing uppercase
    with pytest.raises(Exception) as exc4:
        AuthService.create_user(db_session, UserCreate(username="validuser", password="password123", display_name="User"))
    assert "uppercase" in str(exc4.value)

    # 5. Password missing lowercase
    with pytest.raises(Exception) as exc5:
        AuthService.create_user(db_session, UserCreate(username="validuser", password="PASSWORD123", display_name="User"))
    assert "lowercase" in str(exc5.value)

    # 6. Password missing digit
    with pytest.raises(Exception) as exc6:
        AuthService.create_user(db_session, UserCreate(username="validuser", password="PasswordOnly", display_name="User"))
    assert "number" in str(exc6.value)

    # 7. Valid user creation
    user = AuthService.create_user(
        db_session,
        UserCreate(username="  Adi123  ", password="SecurePassword123", display_name="Aditi Singh", role="ADMIN"),
    )
    assert user.username == "adi123"  # Normalized lowercase
    assert verify_password("SecurePassword123", user.password_hash)
    assert "SecurePassword123" not in user.password_hash  # Hashed

    # 8. Duplicate username (case-insensitive check)
    with pytest.raises(Exception) as exc7:
        AuthService.create_user(
            db_session,
            UserCreate(username="ADI123", password="AnotherPassword123", display_name="Aditi Duplicate"),
        )
    assert "already in use" in str(exc7.value)


def test_login_flow_and_enumeration_prevention(client, db_session: Session):
    """Tests: Login success, token issuance, and non-enumerating failure responses."""
    AuthService.create_user(
        db_session,
        UserCreate(username="mentor1", password="StrongPassword123", display_name="Mentor One", role="MENTOR", mentor_id=1),
    )

    # 1. Successful Login
    res = client.post("/api/auth/login", json={"username": "MENTOR1", "password": "StrongPassword123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "mentor1"
    assert data["user"]["role"] == "MENTOR"

    # 2. Existing username + wrong password
    res_wrong_pw = client.post("/api/auth/login", json={"username": "mentor1", "password": "WrongPassword999"})
    assert res_wrong_pw.status_code == 401
    assert res_wrong_pw.json()["detail"] == "Invalid username or password."

    # 3. Nonexistent username + arbitrary password
    res_unknown = client.post("/api/auth/login", json={"username": "unknown_ghost_user", "password": "SomePassword123"})
    assert res_unknown.status_code == 401
    assert res_unknown.json()["detail"] == "Invalid username or password."

    # Verify identical error message (enumeration prevention)
    assert res_wrong_pw.json()["detail"] == res_unknown.json()["detail"]


def test_jwt_claims_and_token_safety(client, db_session: Session):
    """Tests: JWT payload safety (no password, no hash, no student PII)."""
    user = AuthService.create_user(
        db_session,
        UserCreate(username="adminuser", password="AdminPassword123", display_name="Super Admin", role="ADMIN"),
    )
    access_token, raw_refresh, _ = AuthService.create_user_tokens(db_session, user)

    # Decode payload
    payload = decode_access_token(access_token)
    assert payload["sub"] == str(user.id)
    assert payload["username"] == "adminuser"
    assert payload["role"] == "ADMIN"
    assert payload["display_name"] == "Super Admin"

    # Security assertion: No sensitive information in JWT
    assert "password" not in payload
    assert "password_hash" not in payload
    assert "student" not in payload
    assert "notes" not in payload

    # Raw refresh token must NOT be in DB
    ref_record = db_session.query(RefreshToken).first()
    assert ref_record.token_hash != raw_refresh
    assert ref_record.token_hash == hash_refresh_token(raw_refresh)

    # Access JWT string must NOT be stored in DB tables
    assert db_session.query(RefreshToken).filter(RefreshToken.token_hash == access_token).first() is None


def test_jwt_tampering_and_expiration(client, db_session: Session):
    """Tests: Valid, malformed, tampered, expired JWT and invalid signature rejection."""
    user = AuthService.create_user(
        db_session,
        UserCreate(username="testuser", password="ValidPassword123", display_name="Test User", role="MENTOR"),
    )
    valid_token, _, _ = AuthService.create_user_tokens(db_session, user)

    # 1. Valid token succeeds
    r_valid = client.get("/api/auth/me", headers={"Authorization": f"Bearer {valid_token}"})
    assert r_valid.status_code == 200
    assert r_valid.json()["username"] == "testuser"

    # 2. Missing token -> 401
    r_missing = client.get("/api/auth/me")
    assert r_missing.status_code == 401

    # 3. Malformed token -> 401
    r_malformed = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.valid.jwt"})
    assert r_malformed.status_code == 401

    # 4. Tampered token -> 401
    tampered = valid_token[:-4] + "xxxx"
    r_tampered = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tampered}"})
    assert r_tampered.status_code == 401

    # 5. Wrong signing key -> 401
    wrong_key = "wrong_secret_key_that_is_at_least_32_chars_long_1234567890"
    wrong_key_jwt = jwt.encode({"sub": str(user.id), "username": "testuser", "role": "MENTOR", "iat": int(datetime.now(timezone.utc).timestamp()), "exp": int((datetime.now(timezone.utc) + timedelta(minutes=15)).timestamp())}, wrong_key, algorithm="HS256")
    r_wrong_key = client.get("/api/auth/me", headers={"Authorization": f"Bearer {wrong_key_jwt}"})
    assert r_wrong_key.status_code == 401

    # 6. Expired token -> 401
    secret_key = get_jwt_secret_key()
    expired_payload = {
        "sub": str(user.id),
        "username": "testuser",
        "role": "MENTOR",
        "iat": int((datetime.now(timezone.utc) - timedelta(minutes=20)).timestamp()),
        "exp": int((datetime.now(timezone.utc) - timedelta(minutes=5)).timestamp()),
    }
    expired_jwt = jwt.encode(expired_payload, secret_key, algorithm=JWT_ALGORITHM)
    r_expired = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_jwt}"})
    assert r_expired.status_code == 401
    assert "expired" in r_expired.json()["detail"].lower()


def test_refresh_token_rotation_and_revocation(client, db_session: Session):
    """Tests: Refresh token lifecycle, rotation, and logout revocation."""
    user = AuthService.create_user(
        db_session,
        UserCreate(username="rotator", password="RotationPassword123", display_name="Rotator", role="MENTOR"),
    )
    _, refresh_1, _ = AuthService.create_user_tokens(db_session, user)

    # 1. Valid refresh produces NEW access token and NEW refresh token
    res_refresh = client.post("/api/auth/refresh", json={"refresh_token": refresh_1})
    assert res_refresh.status_code == 200
    data_1 = res_refresh.json()
    new_access = data_1["access_token"]
    refresh_2 = data_1["refresh_token"]
    assert refresh_2 != refresh_1

    # 2. Old refresh token (refresh_1) is now REVOKED and rejected
    res_old = client.post("/api/auth/refresh", json={"refresh_token": refresh_1})
    assert res_old.status_code == 401

    # 3. New access token is functional
    r_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert r_me.status_code == 200

    # 4. Logout revokes active refresh token (refresh_2)
    res_logout = client.post("/api/auth/logout", json={"refresh_token": refresh_2})
    assert res_logout.status_code == 200

    # 5. Revoked refresh token rejected on subsequent refresh attempts
    res_after_logout = client.post("/api/auth/refresh", json={"refresh_token": refresh_2})
    assert res_after_logout.status_code == 401


def test_inactive_account_blocked(client, db_session: Session):
    """Tests: Inactive user accounts are blocked from login, refresh, and protected endpoints."""
    user = AuthService.create_user(
        db_session,
        UserCreate(username="active_then_banned", password="ValidPassword123", display_name="Deactivated User", role="MENTOR"),
    )
    access_token, refresh_token, _ = AuthService.create_user_tokens(db_session, user)

    # 1. Works while active
    res_ok = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert res_ok.status_code == 200

    # 2. Deactivate user in database
    user.is_active = False
    db_session.commit()

    # 3. Access token immediately rejected on protected endpoint
    res_banned = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert res_banned.status_code == 401
    assert "deactivated" in res_banned.json()["detail"].lower()

    # 4. Refresh token rotation fails for deactivated user
    res_ref_banned = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert res_ref_banned.status_code == 401

    # 5. Login fails for deactivated user
    res_login_banned = client.post("/api/auth/login", json={"username": "active_then_banned", "password": "ValidPassword123"})
    assert res_login_banned.status_code == 401


def test_database_role_change_takes_effect_immediately(client, db_session: Session):
    """Tests: Database user role changes take effect immediately without requiring token re-issuance."""
    user = AuthService.create_user(
        db_session,
        UserCreate(username="promoted_user", password="ValidPassword123", display_name="Promoted User", role="MENTOR"),
    )
    access_token, _, _ = AuthService.create_user_tokens(db_session, user)

    # 1. As MENTOR, creating a user is forbidden (403)
    res_forbid = client.post(
        "/api/auth/users",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"username": "subuser1", "password": "ValidPassword123", "display_name": "Sub", "role": "MENTOR"},
    )
    assert res_forbid.status_code == 403

    # 2. Promote user to ADMIN in DB
    user.role = UserRoleEnum.ADMIN.value
    db_session.commit()

    # 3. With SAME access token, operation now succeeds because backend queries DB state
    res_promoted = client.post(
        "/api/auth/users",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"username": "subuser1", "password": "ValidPassword123", "display_name": "Sub", "role": "MENTOR"},
    )
    assert res_promoted.status_code == 201


def test_mentor_spoofing_prevented(client, db_session: Session):
    """Tests: Authenticated mentor cannot spoof mentor_id in intervention creation."""
    mentor_user = AuthService.create_user(
        db_session,
        UserCreate(username="mentor_real", password="ValidPassword123", display_name="Real Mentor", role="MENTOR", mentor_id=1),
    )
    access_token, _, _ = AuthService.create_user_tokens(db_session, mentor_user)

    # Mentor submits with spoofed mentor_id = 999
    res = client.post(
        "/api/interventions",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"student_id": 1, "title": "Academic Assistance", "intervention_type": "ACADEMIC_SUPPORT", "status": "PLANNED", "mentor_id": 999},
    )
    assert res.status_code == 201
    # Backend overrides with authenticated mentor_id (1)
    assert res.json()["mentor_id"] == 1


def test_admin_only_rules_and_upload_permissions(client, db_session: Session):
    """Tests: RBAC rules enforcement for ADMIN-only operations."""
    mentor_user = AuthService.create_user(
        db_session,
        UserCreate(username="mentor_staff", password="ValidPassword123", display_name="Staff", role="MENTOR", mentor_id=1),
    )
    admin_user = AuthService.create_user(
        db_session,
        UserCreate(username="admin_staff", password="ValidPassword123", display_name="Admin Staff", role="ADMIN"),
    )
    token_mentor, _, _ = AuthService.create_user_tokens(db_session, mentor_user)
    token_admin, _, _ = AuthService.create_user_tokens(db_session, admin_user)

    # 1. MENTOR cannot update rules (403)
    res_rules_mentor = client.put(
        "/api/rules",
        headers={"Authorization": f"Bearer {token_mentor}"},
        json={"weights": {"attendance": 0.4, "marks": 0.3, "backlogs": 0.2, "fees": 0.05, "trends": 0.05}, "thresholds": {}},
    )
    assert res_rules_mentor.status_code == 403

    # 2. MENTOR cannot upload files (403)
    res_upload_mentor = client.post(
        "/api/uploads/students",
        headers={"Authorization": f"Bearer {token_mentor}"},
        files={"file": ("test.csv", b"student_id,name\n1,Test", "text/csv")},
    )
    assert res_upload_mentor.status_code == 403

    # 3. ADMIN can update rules (200)
    res_rules_admin = client.put(
        "/api/rules",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={"weights": {"attendance": 0.4, "marks": 0.3, "backlogs": 0.2, "fees": 0.05, "trends": 0.05}, "thresholds": {}},
    )
    assert res_rules_admin.status_code == 200


def test_expired_refresh_token_rejected(client, db_session: Session):
    """Tests: Expired refresh token is rejected."""
    user = AuthService.create_user(
        db_session,
        UserCreate(username="expired_ref", password="ValidPassword123", display_name="Exp Ref", role="MENTOR"),
    )
    _, refresh_token, _ = AuthService.create_user_tokens(db_session, user)

    # Manually expire in DB
    ref_record = db_session.query(RefreshToken).first()
    ref_record.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()

    res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 401


def test_cors_headers_and_disallowed_origin(client):
    """Tests: Strict CORS headers and verification that disallowed origins are not permitted."""
    # 1. Allowed origin
    res_allowed = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res_allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"

    # 2. Disallowed origin
    res_disallowed = client.options(
        "/health",
        headers={
            "Origin": "http://malicious-attacker.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res_disallowed.headers.get("access-control-allow-origin") is None


def test_all_sensitive_endpoints_reject_unauthenticated_requests(client):
    """
    CRITICAL SECURITY TEST:
    Verifies that EVERY institutional data endpoint strictly returns HTTP 401 Unauthorized
    when no Authorization header is provided, leaking zero student or institutional data.
    """
    endpoints_to_test = [
        # Dashboard
        ("GET", "/api/dashboard/overview", None),
        ("GET", "/api/dashboard/departments", None),
        # Students
        ("GET", "/api/students", None),
        ("GET", "/api/students/1", None),
        # Assessment
        ("GET", "/api/students/1/assessment", None),
        ("POST", "/api/students/1/assessment", None),
        # Notifications
        ("GET", "/api/notifications", None),
        ("GET", "/api/notifications/unread-count", None),
        ("PATCH", "/api/notifications/1/read", None),
        ("PATCH", "/api/notifications/read-all", None),
        # Interventions
        ("GET", "/api/interventions", None),
        ("GET", "/api/interventions/summary", None),
        ("GET", "/api/interventions/effectiveness/summary", None),
        ("GET", "/api/interventions/follow-ups", None),
        ("GET", "/api/interventions/1", None),
        ("GET", "/api/interventions/1/effectiveness", None),
        ("POST", "/api/interventions", {"student_id": 1, "title": "Test", "intervention_type": "COUNSELLING", "status": "PLANNED"}),
        ("PATCH", "/api/interventions/1", {"title": "Update"}),
        ("DELETE", "/api/interventions/1", None),
        # Rules
        ("GET", "/api/rules", None),
        ("PUT", "/api/rules", {"weights": {"attendance": 0.4, "marks": 0.3, "backlogs": 0.2, "fees": 0.05, "trends": 0.05}, "thresholds": {}}),
        # Uploads
        ("POST", "/api/uploads/students", None),
        # Auth protected
        ("GET", "/api/auth/me", None),
        ("POST", "/api/auth/users", {"username": "newuser", "password": "Password123", "display_name": "New User"}),
    ]

    for method, path, payload in endpoints_to_test:
        if method == "GET":
            res = client.get(path)
        elif method == "POST":
            res = client.post(path, json=payload)
        elif method == "PATCH":
            res = client.patch(path, json=payload)
        elif method == "PUT":
            res = client.put(path, json=payload)
        elif method == "DELETE":
            res = client.delete(path)
        else:
            raise ValueError(f"Unknown method {method}")

        assert res.status_code == 401, (
            f"SECURITY VULNERABILITY: Endpoint {method} {path} returned {res.status_code} "
            f"instead of 401 Unauthorized for unauthenticated request! Body: {res.text}"
        )
        assert "institutional" not in res.text.lower()
        assert "students" not in res.json().get("detail", "").lower() or "missing or invalid" in res.json().get("detail", "").lower()


def test_public_endpoints_accessible_without_auth(client):
    """Verifies that only genuinely public health, root, and auth handshake routes are accessible without auth."""
    # Health check
    res_health = client.get("/health")
    assert res_health.status_code == 200

    # Root API metadata
    res_root = client.get("/")
    assert res_root.status_code == 200

    # Username availability checker
    res_check = client.get("/api/auth/check-username?username=randomtestuser123")
    assert res_check.status_code == 200

