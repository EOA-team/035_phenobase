import pandas as pd
import os
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

import smbclient
from fastapi import HTTPException, UploadFile, status
from pydantic import RootModel, ValidationError, TypeAdapter

from src.models import CropTypeDelete, CropTypeInsert, CropTypeUpdate
from src.nas_helper import (
    Password as NasPw,
)
from src.nas_helper import (
    User as NasUser,
)
from src.nas_helper import (
    build_unc_path,
    connect_to_nas,
)

NAS_UPLOAD_FOLDER = r"drone\phenobase\production\uploads"


class FileType(StrEnum):
    """Phenobase API supported file types."""

    CSV = "csv"
    GEOJSON = "geojson"


class UploadTables(StrEnum):
    """Phenobase API supported tables for Upload"""

    CROP_TYPE = "crop_type"
    CROP_PLOT = "crop_plot"


TABLE_FILETYPE_MAPPING = {
    UploadTables.CROP_TYPE: FileType.CSV,
    UploadTables.CROP_PLOT: FileType.GEOJSON,
}

CropTypeUploadRow = RootModel[CropTypeInsert | CropTypeUpdate | CropTypeDelete]

# Mapping each UploadTable to its corresponding Pydantic model for validation
UPLOAD_SCHEMA_REGISTRY: dict[UploadTables, type[RootModel]] = {
    UploadTables.CROP_TYPE: CropTypeUploadRow,
}


def build_nas_upload_filename(table_name: UploadTables) -> str:
    """Build a filename for uploading to the NAS
    based on the current timestamp (UTC), table name, and file type."""
    now = datetime.now(tz=UTC)
    date_part = now.strftime("%Y%m%d_%H%M%S")  # 20260822_185612
    ms = now.microsecond // 1000  # microseconds -> milliseconds (0-999)
    filetype = get_supported_filetype(table_name)
    return f"{date_part}_{ms:03d}_{table_name}.{filetype.value}"


def get_supported_filetype(table_name: UploadTables) -> FileType:
    """Get the supported file types for a given table."""
    return TABLE_FILETYPE_MAPPING.get(table_name)


def validate_input_file(
    table_name: UploadTables,
    upload_file: UploadFile,
) -> None:
    """Validate the input file for uploading to the Data Platform."""
    supported_table_names = tuple(UploadTables.value for UploadTables in UploadTables)
    supported_filetype = get_supported_filetype(UploadTables(table_name))

    filetype = upload_file.filename.split(".")[-1]

    if table_name not in supported_table_names:
        raise HTTPException(status_code=400, detail=f"Invalid table name: {table_name}")
    if not upload_file.filename.endswith(supported_filetype.value):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format *.{filetype} for table '{table_name}'."
            f"Spported file format:*.{supported_filetype.value}",
        )
    validation_schema = UPLOAD_SCHEMA_REGISTRY.get(UploadTables(table_name))
    if not validation_schema:
        raise HTTPException(
            status_code=400,
            detail=f"No validation schema found for table '{table_name}'",
        )

    errors = []
 
    try:
        df = pd.read_csv(
            upload_file.file, 
            sep= None, # Pandas auto sniffs the separator
            engine="python",
            encoding="utf-8-sig", #automatically remove Excel BOM artifacts safely
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse CSV file: {str(e)}",
        )
    finally:
        upload_file.file.seek(0)  # Reset file pointer to the beginning for re-reading

    list_adapter = TypeAdapter(list[validation_schema])

    upload_file.file.seek(0)  # Reset file pointer to the beginning for re-reading


    try :
        list_adapter.validate_python(df.to_dict(orient="records"))
    except ValidationError as batch_error:
        for err in batch_error.errors(include_url=False, include_context=False):
            row_index = err.get("loc", [None])[0]
            errors.append(
                {
                    "line": row_index + 2,  # +2 to account for header and 0-indexing
                    "errors": err.get("msg", "Unknown validation error"),
                }
            )

def upload_file_to_nas(table_name: UploadTables, upload_file: UploadFile) -> None:
    """Upload a file to the NAS"""
    upload_path = build_unc_path(
        hostname=os.getenv("NAS_RECKENHOLZ"),
        share="Data-EODrone",
        folder=NAS_UPLOAD_FOLDER,
    )
    filename = build_nas_upload_filename(UploadTables(table_name))
    upload_file_path = Path(upload_path) / filename

    connect_to_nas(user_type=NasUser.SERVICE, password=NasPw.SERVICE)
    with smbclient.open_file(upload_file_path, "wb", encoding="utf-8") as f:
        f.write(upload_file.file.read())
