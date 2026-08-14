"""Unit tests for the Phenobase Dataplatform API endpoints."""

# Testclient allows to test API endpoints without having to run the server.
from fastapi.testclient import TestClient

from src.main import app


def test_health_check():
    """Health endpoint returns 200 with status ok."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_info():
    """Root endpoint returns 200 with correct API information."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == app.title
    assert data["version"] == app.version
    assert data["description"] == app.description


