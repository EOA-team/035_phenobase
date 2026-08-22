from datetime import UTC, datetime
from enum import StrEnum


class FileType(StrEnum):
    """Phenobase API supported file types."""

    CSV = "csv"
    GEOJSON = "geojson"


class Tables(StrEnum):
    """Phenobase API supported tables for Upload"""

    CROP_TYPE = "crop_type"
    CROP_PLOT = "crop_plot"


TABLE_FILETYPE_MAPPING = {
    Tables.CROP_TYPE: FileType.CSV,
    Tables.CROP_PLOT: FileType.GEOJSON,
}


def build_nas_upload_filename(table_name: Tables) -> str:
    """Build a filename for uploading to the NAS
    based on the current timestamp (UTC), table name, and file type."""
    now = datetime.now(tz=UTC)
    date_part = now.strftime("%Y%m%d_%H%M%S")  # 20260822_185612
    ms = now.microsecond // 1000  # microseconds -> milliseconds (0-999)
    filetype = get_supported_filetype(table_name)
    return f"{date_part}_{ms:03d}_{table_name}.{filetype.value}"


def get_supported_filetype(table_name: Tables) -> FileType:
    """Get the supported file types for a given table."""
    return TABLE_FILETYPE_MAPPING.get(table_name)
