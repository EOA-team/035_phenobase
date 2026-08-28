"""Unit tests for the Phenobase Dataplatform API endpoints."""

# Testclient allows to test API endpoints without having to run the server.
import io
import os
from pathlib import Path

import pandas as pd
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from src.main import app

load_dotenv()

TEST_CSVS_FOLDER = Path(__file__).parent / "test_csvs"


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
    assert data["status"] == "active"
    assert data["role"] == "reader"
    assert data["email"] == "hans.mueller@example.com"
    assert "key_hash" not in data  # Ensure key_hash is not returned in the response


@pytest.mark.integration_test
def test_auth_me_invalid(phenobase_db_minimal):
    """Test the /auth/me endpoint with an invalid API key."""
    client = TestClient(app)
    headers = {"X-API-Key": "a_wrong_api_key"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API key"}


@pytest.mark.integration_test
def test_generate_api_key(phenobase_db_minimal):
    """Test the /admin/generate-api-key endpoint."""
    client = TestClient(app)
    headers = {"X-API-Key": os.getenv("SABRINA_SCHINDLER_API_KEY")}
    response = client.get("/admin/generate-api-key", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["api_key"] is not None
    assert data["key_hash"] is not None

    headers = {"X-API-Key": os.getenv("MAX_MUSTERMANN_API_KEY")}
    response = client.get("/admin/generate-api-key", headers=headers)
    assert response.status_code == 403


@pytest.mark.integration_test
def test_insert_and_delete(phenobase_db_minimal):
    """Test the POST /data/upload/{table_name} with INSERT and DELETE operations,
    then verify with GET /data/{table_name}"""
    csv_file_name = "unit_tbl_upload_dirty.csv"
    csv_file_path = TEST_CSVS_FOLDER / csv_file_name

    client = TestClient(app)
    x_api_key_header = {"X-API-Key": os.getenv("MAX_MUSTERMANN_API_KEY")}
    response = client.post(
        "data/upload/unit",
        headers=x_api_key_header,
        files={"upload_file": (csv_file_name, csv_file_path.read_bytes(), "text/csv")},
    )
    assert response.status_code == 200

    response = client.get("data/unit", headers=x_api_key_header)
    df = pd.read_csv(io.BytesIO(response.content), sep=";")

    deleted_ids = df.query("id in [1,4]")
    inserted_id2 = df.query("id == 2")
    inserted_id3 = df.query("id == 3")

    assert deleted_ids.empty
    assert inserted_id2.iloc[0]["name"] == "Meter"
    assert inserted_id3.iloc[0]["code"] == "kg"
