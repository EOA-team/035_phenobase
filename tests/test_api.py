"""Unit tests for the Phenobase Dataplatform API endpoints."""

# Testclient allows to test API endpoints without having to run the server.
import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from src.main import app

load_dotenv()


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


@pytest.mark.integration_test
def test_auth_me_valid(phenobase_db_minimal):
    """Test the /auth/me endpoint with a valid API key."""
    client = TestClient(app)

    headers = {"X-API-Key": os.getenv("HANS_MUELLER_API_KEY")}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" not in data  # Ensure id is not returned in the response
    assert data["f_account"] == "F12345678"
    assert data["firstname"] == "Hans "
    assert data["lastname"] == "Müller"
    assert data["role"] == "reader"
    assert data["email"] == "hans.mueller@example.com"
    assert "key_hash" not in data  # Ensure key_hash is not returned in the response


@pytest.mark.integration_test
def test_auth_me_invalid():
    """Test the /auth/me endpoint with an invalid API key."""
    client = TestClient(app)
    headers = {"X-API-Key": "a_wrong_api_key"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API key"}
