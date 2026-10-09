from datetime import UTC, datetime
from pathlib import Path, PureWindowsPath
from typing import Any, Protocol, cast

import pandas as pd
import smbclient
from fastapi import HTTPException, UploadFile, status
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, Session

from src.models.base import (
    UploadModes,
)
from src.models.registry import (
    SCHEMA_REGISTRY,
    CsvTables,
    ManagedTables,
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
from src.settings import DeployStage, Infrastructure, Settings


class UploadRecord(Protocol):
    """Structural type for Insert/Update/Delete upload models."""

    mode: object

    def model_dump(self, **kwargs: Any) -> dict[str, Any]: ...


class UploadRecordWithId(UploadRecord, Protocol):
    """Upload model that also carries a primary key (Update/Delete)."""

    id: int


def build_local_upload_path(base_path: str, deploy_stage: DeployStage) -> Path:
    """Build the upload path on local storage."""
    return Path(base_path) / deploy_stage.value / "uploads"


def build_unc_upload_path(base_path: str, deploy_stage: DeployStage) -> PureWindowsPath:
    """Build the upload path on the NAS. Always uses backslashes, whatever the OS."""
    return PureWindowsPath(base_path) / deploy_stage.value / "uploads"


def build_upload_filename(table_name: ManagedTables) -> str:
    """Build a filename for upload
    based on the current timestamp (UTC), table name, and file type."""
    now = datetime.now(tz=UTC)
    date_part = now.strftime("%Y%m%d_%H%M%S")  # 20260822_185612
    ms = now.microsecond // 1000  # microseconds -> milliseconds (0-999)
    filetype = SCHEMA_REGISTRY[table_name].filetype
    if filetype is None:
        raise ValueError(
            f"Table '{table_name.value}' is derived and has no upload file type."
        )
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
    raw_df.columns = raw_df.columns.str.lower()  # Lower on headers
    raw_df.columns = raw_df.columns.str.strip()  # Strip whitespace on headers
    # Strip whitespace (e.g. modes " insert" or "update " instead of "insert" or "update")
    raw_df = raw_df.map(lambda x: x.strip() if isinstance(x, str) else x)
    # Make sure "Insert" or "Update" is treated the same as "insert" or "update" (lowercase)
    if "mode" in raw_df.columns:
        raw_df["mode"] = raw_df["mode"].str.lower()  # Lower on modes
    # Replace pandas NA and NaN with None for consistency
    df = raw_df.replace({pd.NA: None, float("nan"): None})

    upload_file.file.seek(0)  # Reset file pointer to the beginning for re-reading
    return df


def append_user_ids(
    df: pd.DataFrame, current_user_id: int, current_user: str
) -> pd.DataFrame:
    """Append user IDs to the DataFrame based on the table name.
    The pydantic upload models will use creator_id on insert and updater_id on update, so we add both here."""
    df["creator_id"] = current_user_id
    df["updater_id"] = current_user_id
    df["user"] = current_user
    return df


def validate_uploaded_file(table_name: ManagedTables, upload_file: UploadFile) -> None:
    """Validate the input file for uploading to the Data Platform."""
    schema = SCHEMA_REGISTRY.get(ManagedTables(str(table_name)))
    if schema is None:
        raise HTTPException(
            status_code=400, detail=f"Unsupported table for upload: {table_name}"
        )
    if schema.filetype is None:
        raise HTTPException(
            status_code=400,
            detail=f"Table '{table_name.value}' has no upload file type.",
        )
    if upload_file.filename is None:
        raise HTTPException(
            status_code=400, detail="Missing filename in the uploaded file."
        )
    filetype = upload_file.filename.split(".")[-1]
    if not upload_file.filename.endswith(schema.filetype.value):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format *.{filetype} for table '{table_name}'. "
            f"Supported file format: *.{schema.filetype.value}",
        )


def validate_file_content(
    df: pd.DataFrame, table_name: CsvTables
) -> list[UploadRecord]:
    """Validate the data in the DataFrame against the corresponding Pydantic upload model.
    The upload model is determined based on the table name using the SCHEMA_REGISTRY.
    """

    validation_schema = SCHEMA_REGISTRY.get(ManagedTables(str(table_name)))
    if not validation_schema:
        raise HTTPException(
            status_code=400,
            detail=f"No validation schema found for table '{table_name}'",
        )

    validated: list[UploadRecord] = []
    errors = []
    failed_rows = 0

    upload_adapter: TypeAdapter[UploadRecord] = TypeAdapter(
        validation_schema.upload_model
    )

    records = df.to_dict(orient="records")
    for index, record in enumerate(records):
        try:
            validated.append(upload_adapter.validate_python(record))

        except ValidationError as row_error:
            failed_rows += 1
            line = index + 2  # +2 to account for header and 0-indexing
            for err in row_error.errors(include_url=False, include_context=False):
                errors.append(
                    {
                        "code": err.get("type", "value_error"),
                        "loc": ["line", line, *err.get("loc", ())],
                        "msg": err.get("msg", "Unknown validation error"),
                    }
                )

    if failed_rows:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "type": "validation_error",
                "title": "File validation failed",
                "failed_rows": failed_rows,
                "errors": errors,
            },
        )
    return validated


def write_file_to_storage(table_name: ManagedTables, data: bytes) -> None:
    """Upload a file to the storage location (NAS or local) based on the infrastructure setting."""

    def _write_to_local_storage(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def _write_to_nas_storage(path: PureWindowsPath, data: bytes) -> None:
        connect_to_nas(user_type=NasUser.SERVICE, password=NasPw.SERVICE)
        smbclient.makedirs(str(path.parent), exist_ok=True)  # create folder if missing
        with smbclient.open_file(
            str(path), mode="wb"
        ) as f:  # no encoding in binary mode
            f.write(data)

    settings = Settings()
    filename = build_upload_filename(ManagedTables(str(table_name)))

    if settings.infrastructure == Infrastructure.LOCAL:
        local_upload_path = build_local_upload_path(
            base_path=settings.storage.local_path,
            deploy_stage=settings.deploy_stage,
        )
        _write_to_local_storage(local_upload_path / filename, data)
    elif settings.infrastructure == Infrastructure.AGS_FOLA:
        unc_path = build_unc_path(
            hostname=settings.storage.host,
            share=settings.storage.share,
            folder=settings.storage.folder,
        )
        nas_upload_path = build_unc_upload_path(
            base_path=unc_path,
            deploy_stage=settings.deploy_stage,
        )
        _write_to_nas_storage(nas_upload_path / filename, data)
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Unsupported infrastructure: {settings.infrastructure}",
        )


def apply_rows(
    session: Session,
    table_name: ManagedTables,
    rows: list[UploadRecord],
) -> list[SQLModel]:
    """Apply rows (insert/update/delete) WITHOUT committing.

    Works for any table registered in SCHEMA_REGISTRY: the target
    table class comes from the registry, and each upload model carries its
    own fields, so model_dump() always produces valid column values.

    The session is flushed at the end so surrogate (auto-increment) ids are
    available to callers while nothing is persisted before the commit.
    Returns the row instances for insert and update rows.
    """
    table = SCHEMA_REGISTRY[table_name].table_model
    results: list[SQLModel] = []

    for row in rows:
        mode = row.mode  # every Insert/Update/Delete model has one

        if mode == UploadModes.INSERT:
            instance = table(**row.model_dump(exclude={"mode"}))
            session.add(instance)
            results.append(instance)

        elif mode == UploadModes.UPDATE:
            row_id = cast(
                "UploadRecordWithId", row
            ).id  # guaranteed by validate_file_content
            existing = session.get(table, row_id)
            if existing is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Cannot update: {table.__tablename__} id={row_id} does not exist",
                )
            for field, value in row.model_dump(exclude={"mode", "id"}).items():
                setattr(existing, field, value)
            results.append(existing)

        elif mode == UploadModes.DELETE:
            row_id = cast(
                "UploadRecordWithId", row
            ).id  # guaranteed by validate_file_content
            existing = session.get(table, row_id)
            if existing is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Cannot delete: {table.__tablename__} id={row_id} does not exist",
                )
            session.delete(existing)

    session.flush()
    return results


def commit_or_conflict(session: Session) -> None:
    """Commit the session; on a constraint violation rollback + 409.

    Keeps whole-file atomicity: either the caller's rows land or none does.
    """
    try:
        session.commit()
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Database constraint violation: {_integrity_error_detail(err)}",
        ) from err


def write_to_database(
    session: Session,
    table_name: ManagedTables,
    rows: list[UploadRecord],
) -> None:
    """Write validated rows to the database as insert/update/delete.

    All rows are applied within one session; a single commit at the end
    makes the whole file atomic: either every row lands or none does.
    """
    apply_rows(session, table_name, rows)
    commit_or_conflict(session)


def _integrity_error_detail(err: IntegrityError) -> str:
    diag = getattr(err.orig, "diag", None)
    primary = getattr(diag, "message_primary", None)
    detail = getattr(diag, "message_detail", None)
    if primary and detail:
        return f"{primary} ({detail})"
    return detail or primary or str(err.orig)


def build_upload_csv_template(table_name: CsvTables) -> str:
    """Generates a csv template for data upload on the given table_name,
    based on the base model in SCHEMA_REGISTRY."""

    validation_schema = SCHEMA_REGISTRY.get(ManagedTables(str(table_name)))
    if validation_schema is None:
        raise HTTPException(
            status_code=400, detail=f"Unsupported table for upload: {table_name}"
        )
    row_model = validation_schema.base_model
    base_column = list(row_model.model_fields.keys())
    columns = ["id", "mode", *base_column]

    insert_row = ["", "insert", *["PLACEHOLDER" for _ in base_column]]
    delete_row = ["PLACEHOLDER", "delete", *["" for _ in base_column]]
    update_row = ["PLACEHOLDER", "update", *["PLACEHOLDER" for _ in base_column]]

    rows = [columns, insert_row, update_row, delete_row]

    return "\n".join(";".join(row) for row in rows) + "\n"


if __name__ == "__main__":
    settings = Settings()
    deploy_stage = settings.deploy_stage
    infrastructure = settings.infrastructure

    local_path = settings.storage.local_path
    unc_path = build_unc_path(
        hostname=settings.storage.host,
        share=settings.storage.share,
        folder=settings.storage.folder,
    )

    print(build_local_upload_path(base_path=local_path, deploy_stage=deploy_stage))
    print(build_unc_upload_path(base_path=unc_path, deploy_stage=deploy_stage))
