from datetime import UTC, datetime
from pathlib import Path, PureWindowsPath

import smbclient
from fastapi import HTTPException

from src.models.registry import (
    SCHEMA_REGISTRY,
    UploadTables,
)
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


def write_logfile(table_name: UploadTables, data: bytes) -> None:
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
