import pytest
from fastapi.testclient import TestClient

try:
    from app.main import app
except ImportError:
    from backend.app.main import app

client = TestClient(app)

def test_docs_endpoint():
    """Verify that GET /docs returns 200 OK."""
    res = client.get("/docs")
    assert res.status_code == 200

def test_openapi_json_endpoint():
    """Verify that GET /openapi.json returns 200 OK and contains core Pathwise endpoints."""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()

    assert schema["info"]["title"] == "Pathwise API"
    paths = schema["paths"]

    # Core endpoint presence check
    assert "/health" in paths
    assert "/" in paths
    assert "/api/students" in paths
    assert "/api/students/{student_id}" in paths
    assert "/api/students/{student_id}/assessment" in paths
    assert "/api/dashboard/overview" in paths
    assert "/api/dashboard/departments" in paths
    assert "/api/rules" in paths
    assert "/api/uploads/{data_type}" in paths
