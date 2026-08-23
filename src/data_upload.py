import os
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from types import UnionType

import pandas as pd
import smbclient
from fastapi import HTTPException, UploadFile, status
from pydantic import BaseModel, TypeAdapter, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel

from src.models import (
    CropType,
    CropTypeDelete,
    CropTypeInsert,
    CropTypeUpdate,
    UploadModes,
)
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


@dataclass(frozen=True)
class UploadSchema:
    """Configuration for one uploadable table.

    row_model:    Pydantic model (or union of insert/update/delete models) used to
                  validate each uploaded record.
    table_model:  SQLModel class (declared with table=True) the validated records
                  are written to.
    filetype:     File format the API accepts for this table.
    """

    row_model: type[BaseModel] | UnionType
    table_model: type[SQLModel]
    filetype: FileType

    def __post_init__(self) -> None:
        # SQLAlchemy attaches __table__ only to classes declared with table=True,
        # so this guards against accidentally registering a non-table model.
        if getattr(self.table_model, "__table__", None) is None:
            raise TypeError(
                f"{self.table_model.__name__} is not a SQLModel table "
                f"(missing table=True / __table__)."
            )


# Configuration for each uploadable table: row model(s), target table, and accepted filetype.
UPLOAD_SCHEMA_REGISTRY: dict[UploadTables, UploadSchema] = {
    UploadTables.CROP_TYPE: UploadSchema(
        row_model=CropTypeInsert | CropTypeUpdate | CropTypeDelete,
        table_model=CropType,
        filetype=FileType.CSV,
    ),
}


def build_nas_upload_filename(table_name: UploadTables) -> str:
    """Build a filename for uploading to the NAS
    based on the current timestamp (UTC), table name, and file type."""
    now = datetime.now(tz=UTC)
    date_part = now.strftime("%Y%m%d_%H%M%S")  # 20260822_185612
    ms = now.microsecond // 1000  # microseconds -> milliseconds (0-999)
    filetype = UPLOAD_SCHEMA_REGISTRY[table_name].filetype
    return f"{date_part}_{ms:03d}_{table_name}.{filetype.value}"


def read_upload_file(upload_file: UploadFile) -> pd.DataFrame:
    """Read the uploaded file into a pandas DataFrame based on its file type."""
    raw_df = pd.read_csv(
        upload_file.file,
        sep=None,  # Pandas auto sniffs the separator
        engine="python",
        encoding="utf-8-sig",  # automatically remove Excel BOM artifacts safely
    )

    # Basic Clearning
    raw_df.columns = raw_df.columns.str.lower()
    raw_df.columns = raw_df.columns.str.strip()
    # Replace pandas NA and NaN with None for consistency
    df = raw_df.replace({pd.NA: None, float("nan"): None})

    upload_file.file.seek(0)  # Reset file pointer to the beginning for re-reading
    return df


def append_user_ids(
    df: pd.DataFrame, current_user_id: int, current_user: str
) -> pd.DataFrame:
    """Append user IDs to the DataFrame based on the table name.
    The pydantic row models will use creato_id on insert and updater_id on update, so we add both here."""
    df["creator_id"] = current_user_id
    df["updater_id"] = current_user_id
    df["user"] = current_user
    return df


def validate_uploaded_file(table_name: UploadTables, upload_file: UploadFile) -> None:
    """Validate the input file for uploading to the Data Platform."""
    schema = UPLOAD_SCHEMA_REGISTRY.get(table_name)
    if schema is None:
        raise HTTPException(
            status_code=400, detail=f"Unsupported table for upload: {table_name}"
        )

    filetype = upload_file.filename.split(".")[-1]
    if not upload_file.filename.endswith(schema.filetype.value):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format *.{filetype} for table '{table_name}'. "
            f"Supported file format: *.{schema.filetype.value}",
        )


def validate_file_content(
    df: pd.DataFrame, table_name: UploadTables
) -> list[BaseModel]:
    """Validate the data in the DataFrame against the corresponding Pydantic row model.
    The row model is determined based on the table name using the UPLOAD_SCHEMA_REGISTRY.
    """

    validation_schema = UPLOAD_SCHEMA_REGISTRY.get(UploadTables(table_name))
    if not validation_schema:
        raise HTTPException(
            status_code=400,
            detail=f"No validation schema found for table '{table_name}'",
        )

    errors = []
    validated = []

    row_adapter = TypeAdapter(validation_schema.row_model)

    records = df.to_dict(orient="records")
    for index, record in enumerate(records):
        try:
            validated.append(row_adapter.validate_python(record))

        except ValidationError as row_error:
            line = index + 2  # +2 to account for header and 0-indexing
            for err in row_error.errors(include_url=False, include_context=False):
                errors.append(
                    {
                        "type": err.get("type", "value_error"),
                        "loc": ("line", line, *err.get("loc", ())),
                        "msg": err.get("msg", "Unknown validation error"),
                        "input": record,
                    }
                )
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=errors
        )
    return validated


def write_file_to_nas(table_name: UploadTables, data: bytes) -> None:
    """Upload a any file to the NAS"""
    upload_path = build_unc_path(
        hostname=os.getenv("NAS_RECKENHOLZ"),
        share="Data-EODrone",
        folder=NAS_UPLOAD_FOLDER,
    )
    filename = build_nas_upload_filename(UploadTables(table_name))
    upload_file_path = Path(upload_path) / filename

    connect_to_nas(user_type=NasUser.SERVICE, password=NasPw.SERVICE)
    with smbclient.open_file(upload_file_path, "wb", encoding="utf-8") as f:
        f.write(data)


def write_to_database(
    session: Session,
    table_name: UploadTables,
    rows: list[BaseModel],
) -> None:
    """Write validated rows to the database as insert/update/delete.

    Works for any table registered in UPLOAD_SCHEMA_REGISTRY: the target
    table class comes from the registry, and each row model carries its
    own fields, so model_dump() always produces valid column values.

    All rows are applied within one session; a single commit at the end
    makes the whole file atomic: either every row lands or none does.
    """
    table = UPLOAD_SCHEMA_REGISTRY[table_name].table_model

    for row in rows:
        mode = row.mode  # every Insert/Update/Delete model has one

        if mode == UploadModes.INSERT:
            session.add(table(**row.model_dump(exclude={"mode"})))

        elif mode == UploadModes.UPDATE:
            row_id = row.id
            existing = session.get(table, row_id)
            if existing is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Cannot update: {table.__tablename__} id={row_id} does not exist",
                )
            for field, value in row.model_dump(exclude={"mode", "id"}).items():
                setattr(existing, field, value)

        elif mode == UploadModes.DELETE:
            row_id = row.id
            existing = session.get(table, row_id)
            if existing is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Cannot delete: {table.__tablename__} id={row_id} does not exist",
                )
            session.delete(existing)

    try:
        session.commit()
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Database constraint violation: {_integrity_error_detail(err)}",
        ) from err


def _integrity_error_detail(err: IntegrityError) -> str:
    diag = getattr(err.orig, "diag", None)
    primary = getattr(diag, "message_primary", None)
    detail = getattr(diag, "message_detail", None)
    if primary and detail:
        return f"{primary} ({detail})"
    return detail or primary or str(err.orig)
