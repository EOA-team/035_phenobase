import io
import os
from pathlib import Path

import pandas as pd
from fastapi import UploadFile
from sqlmodel import Session, select

from src.auth import hash_api_key
from src.data_upload import (
    append_user_ids,
    read_upload_file,
    validate_file_content,
    validate_uploaded_file,
    write_to_database,
)
from src.db_utils import get_db_table_as_pd
from src.models.registry import UploadTables
from src.models.tables.user import User

TEST_CSVS_FOLDER = Path(__file__).parent / "test_csvs"


def _make_upload_file(path: Path) -> UploadFile:
    """Wrap a file from disk in a FastAPI UploadFile (BytesIO supports .seek)."""
    return UploadFile(file=io.BytesIO(path.read_bytes()), filename=path.name)


def _get_user_by_api_key(session: Session, api_key: str) -> User | None:
    """Retrieve a user from the database based on the provided API key."""
    key_hash = hash_api_key(api_key)
    statement = select(User).where(User.key_hash == key_hash)
    user = session.exec(statement).one_or_none()
    return user


def test_get_user_by_api_key(phenobase_db_minimal_sqlite):
    with phenobase_db_minimal_sqlite as session:
        user = _get_user_by_api_key(
            session, api_key=os.getenv("MAX_MUSTERMANN_API_KEY")
        )

        assert user.f_account == "F23456781"
        assert user.firstname == "Max"
        assert user.lastname == "Mustermann"


def test_read_upload_file():
    """Test the read_upload_file function cleans the uploaded CSV file correctly."""
    original_csv = TEST_CSVS_FOLDER / "unit_tbl_upload_dirty.csv"
    expected_csv = TEST_CSVS_FOLDER / "unit_tbl_upload_clean.csv"

    df_cleaned = read_upload_file(_make_upload_file(original_csv))
    df_expected = read_upload_file(_make_upload_file(expected_csv))

    pd.testing.assert_frame_equal(df_cleaned, df_expected, check_dtype=True)


def test_full_upload_process(phenobase_db_minimal_sqlite):
    """Test the full upload process with SQLite in-memory database."""
    upload_csv = _make_upload_file(TEST_CSVS_FOLDER / "unit_tbl_upload_clean.csv")
    unit_tbl_name = UploadTables.UNIT
    validate_uploaded_file(upload_file=upload_csv, table_name=unit_tbl_name)

    user = None
    with phenobase_db_minimal_sqlite as session:
        user = _get_user_by_api_key(
            session, api_key=os.getenv("MAX_MUSTERMANN_API_KEY")
        )

        df = read_upload_file(upload_file=upload_csv).pipe(
            append_user_ids,
            current_user_id=user.id,
            current_user=user.firstname + " " + user.lastname,
        )

        validated_rows = validate_file_content(df=df, table_name=unit_tbl_name)
        write_to_database(
            session=session, table_name=unit_tbl_name, rows=validated_rows
        )
        df_db = get_db_table_as_pd(session=session, table_name=unit_tbl_name)

        deleted_ids = df_db.query("id in [1,4]")
        inserted_id2 = df_db.query("id == 2")
        inserted_id3 = df_db.query("id == 3")

        assert deleted_ids.empty
        assert inserted_id2.iloc[0]["name"] == "Meter"
        assert inserted_id3.iloc[0]["code"] == "kg"
