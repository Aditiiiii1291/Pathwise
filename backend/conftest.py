import os
import pytest
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User, UserRoleEnum

# Ensure a secure environment test key is loaded for pytest runs
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "pytest_test_environment_secure_jwt_secret_key_at_least_64_bytes_long_2026_abcd1234",
)
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")


@pytest.fixture(autouse=True)
def default_auth_override(request):
    """
    For domain and business logic tests outside test_auth.py, inject an active ADMIN user
    so business logic tests run as authenticated institutional staff.
    test_auth.py explicitly tests real unauthenticated 401s, token verification, and RBAC.
    """
    if "test_auth" in request.node.nodeid:
        yield
        return

    admin_user = User(
        id=999,
        username="test_admin",
        role=UserRoleEnum.ADMIN.value,
        display_name="Test Administrator",
        is_active=True,
        mentor_id=None,
    )
    app.dependency_overrides[get_current_user] = lambda: admin_user
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)
