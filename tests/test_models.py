import os

import pandas as pd
import pytest
from dotenv import load_dotenv

from src.auth import get_current_user
from src.db_session import open_db_session
from src.models.base import UploadModes
from src.models.registry import UploadTables
from src.preprocessing import prepare_dataframe
from src.validation import UploadValidationError, validate_file_content

load_dotenv()


def get_max_mustermann():
    """Retrieve the current user based on the provided API key."""
    with open_db_session() as session:
        return get_current_user(
            api_key=os.getenv("MAX_MUSTERMANN_API_KEY"), session=session
        )


def test_insert(phenobase_db_minimal):
    """Test insert model , just testing a few columns, not all of them."""

    data_dict = {
        "mode": UploadModes.INSERT,
        "name": "test_crop",
        "code": "TC001",
        "description": "A test crop type for unit testing.",
        "doc_path": "doc/TC001.pdf",
        "additional_column": "not neeeded.",  # This column should be dropped during validation
    }

    raw_df = pd.DataFrame([data_dict])
    prep_df = prepare_dataframe(parsed_df=raw_df, user=get_max_mustermann())

    # Additional column should be dropped during validation
    validated_entry = validate_file_content(
        df=prep_df, table_name=UploadTables.CROP_TYPE
    )[0]
    assert not hasattr(validated_entry, "additional_column")

    # Doc Path is optional, so we can drop it and still expect a validation success
    prep_df = prep_df.drop(columns=["doc_path"], errors="ignore")
    result = validate_file_content(df=prep_df, table_name=UploadTables.CROP_TYPE)
    assert len(result) == 1

    # creator_id is required
    prep_df = prep_df.drop(columns=["creator_id"], errors="ignore")
    with pytest.raises(UploadValidationError):
        validate_file_content(df=prep_df, table_name=UploadTables.CROP_TYPE)


def test_delete(phenobase_db_minimal):
    """Test delete model, just testing a few columns, not all of them."""

    data_dict = {
        "mode": UploadModes.DELETE,
        "id": 1,
        "additional_column": "not neeeded.",  # This column should be dropped during validation
    }
    raw_df = pd.DataFrame([data_dict])
    prep_df = prepare_dataframe(parsed_df=raw_df, user=get_max_mustermann())

    # Additional column should be dropped during validation
    validated_entry = validate_file_content(
        df=prep_df, table_name=UploadTables.CROP_TYPE
    )[0]
    assert not hasattr(validated_entry, "additional_column")

    # Id is required
    prep_df = prep_df.drop(columns=["id"], errors="ignore")
    with pytest.raises(UploadValidationError):
        validate_file_content(df=prep_df, table_name=UploadTables.CROP_TYPE)



# def test_update(phenobase_db_minimal):
#     """Test update model, just testing a few columns, not all of them."""
#
#     data_dict = {
#         "mode": UploadModes.UPDATE,
#         "id": 1,
#         "name": "test_crop",
#         "code": "TC001",
#         "description": "A test crop type for unit testing.",
#         "doc_path": "doc/TC001.pdf",
#         "additional_column": "not neeeded.",  # This column should be dropped during validation
#     }
#     raw_df = pd.DataFrame([data_dict])
#     prep_df = prepare_dataframe(parsed_df=raw_df, user=get_max_mustermann())
#     print(prep_df)
#
#     # Additional column should be dropped during validation
#     validated_entry = validate_file_content(
#         df=prep_df, table_name=UploadTables.CROP_TYPE
#     )[0]
#     assert not hasattr(validated_entry, "additional_column")
#
#     # Id is required, so we expect a validation error if we drop it
#     prep_df = prep_df.drop(columns=["name"], errors="ignore")
#     validate_file_content(df=prep_df, table_name=UploadTables.CROP_TYPE)