"""Unit Tests to check pydantic models work"""


import io
import os
from pathlib import Path

import pandas as pd
import pytest
import json
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from src.models.tables.crop_type import CropTypeInsert
from src.data_upload import append_user_ids, validate_file_content, sanitize_null_values, write_to_database
from src.models.registry import UploadTables
from src.models.base import UploadModes
from src.db_utils import get_db_table_as_pd


from src.main import app

TEST_USER_ID = 999
TEST_USER_NAME = "test"

def get_user_info(client: TestClient, api_key: str):
    """Helper function to get user info from the /auth/me endpoint."""
    headers = {"X-API-Key": api_key}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    return response.json()

@pytest.mark.integration
def test_insert_delete_update(phenobase_db_minimal):
    """Test"""
    file_path = Path(__file__).parent / "test_data" / "test_crops.json"

    client = TestClient(app)
    user = get_user_info(client, os.getenv("MAX_MUSTERMANN_API_KEY"))

    # 1. Insert Data
    tmp_df = pd.read_json(file_path, encoding="utf-8")
    tmp_df["mode"] = UploadModes.INSERT

    # 2. Delete Sugar Beet
    delete_df = pd.DataFrame([{"id":2, "mode": UploadModes.DELETE}])

    # 3. Update Name of Temp Grassland only
    update_df1 = pd.DataFrame([{"id": 3, "mode": UploadModes.UPDATE, "name": "grassland"}])

    # 4. Update Code, Name and Doc Path in Soybean
    update_df2 = pd.DataFrame([{"id": 1, "mode": UploadModes.UPDATE,
                                "code": "SYB", "name": "soybean ufa", "doc_path": "/docs/soy_bean"}])

    # Build DF
    tmp_df = pd.concat([tmp_df, delete_df, update_df1, update_df2])
    tmp_df = append_user_ids(
        df=tmp_df,
        current_user=user["firstname"] + " " + user["lastname"],
        current_user_id=user["id"]
    )

    df = sanitize_null_values(df=tmp_df)
    print(df)
    validated_rows = validate_file_content(df=df, table_name=UploadTables.CROP_TYPE)

    write_to_database(
        session=phenobase_db_minimal,
        table_name=UploadTables.CROP_TYPE,
        rows=validated_rows
    )

    read_df = get_db_table_as_pd(
        session=phenobase_db_minimal,
        table_name=UploadTables.CROP_TYPE)

    assert






