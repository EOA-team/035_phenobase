from datetime import UTC, datetime
from pathlib import Path, PureWindowsPath

import pandas as pd
import smbclient
from fastapi import HTTPException, status
from pydantic import TypeAdapter, ValidationError

from src.models.registry import (
    SCHEMA_REGISTRY,
    UploadTables,
)
from src.models.row_models import UploadRow
from src.settings import DeployStage, Infrastructure, Settings
from src.utils.nas_utils import (
    Password as NasPw,
)
from src.utils.nas_utils import (
    User as NasUser,
)
from src.utils.nas_utils import (
    build_unc_path,
    connect_to_nas,
)


def build_local_upload_path(base_path: str, deploy_stage: DeployStage) -> Path:
    """Build the upload path on local storage."""
    return Path(base_path) / deploy_stage.value / "uploads"


def build_unc_upload_path(base_path: str, deploy_stage: DeployStage) -> PureWindowsPath:
    """Build the upload path on the NAS. Always uses backslashes, whatever the OS."""
    return PureWindowsPath(base_path) / deploy_stage.value / "uploads"


def build_upload_filename(table_name: UploadTables) -> str:
    """Build a filename for upload
    based on the current timestamp (UTC), table name, and file type."""
    now = datetime.now(tz=UTC)
    date_part = now.strftime("%Y%m%d_%H%M%S")  # 20260822_185612
    ms = now.microsecond // 1000  # microseconds -> milliseconds (0-999)
    filetype = SCHEMA_REGISTRY[table_name].filetype
    return f"{date_part}_{ms:03d}_{table_name}.{filetype.value}"


def validate_file_content(
    df: pd.DataFrame, table_name: UploadTables
) -> list[UploadRow]:
    """Validate the data in the DataFrame against the corresponding Pydantic row model.
    The row model is determined based on the table name using the SCHEMA_REGISTRY.
    """

    validation_schema = SCHEMA_REGISTRY.get(UploadTables(table_name))
    if not validation_schema:
        raise HTTPException(
            status_code=400,
            detail=f"No validation schema found for table '{table_name}'",
        )

    validated: list[UploadRow] = []
    errors = []
    failed_rows = 0

    row_adapter: TypeAdapter[UploadRow] = TypeAdapter(validation_schema.row_model)

    records = df.to_dict(orient="records")
    for index, record in enumerate(records):
        try:
            validated.append(row_adapter.validate_python(record))

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


def write_file_to_storage(table_name: UploadTables, data: bytes) -> None:
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
    filename = build_upload_filename(UploadTables(table_name))

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
