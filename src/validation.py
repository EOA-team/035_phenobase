import pandas as pd
from pydantic import TypeAdapter, ValidationError

from src.models.registry import (
    SCHEMA_REGISTRY,
    UploadTables,
)
from src.models.row_models import UploadRow


class UploadValidationError(Exception):
    """Row-level validation of an uploaded file failed."""

    def __init__(self, failed_rows: int, errors: list[dict]):
        super().__init__(f"{failed_rows} invalid rows in file")
        self.failed_rows = failed_rows
        self.errors = errors


def validate_file_content(
    df: pd.DataFrame, table_name: UploadTables
) -> list[UploadRow]:
    """Validate the data in the DataFrame against the corresponding Pydantic row model.
    The row model is determined based on the table name using the SCHEMA_REGISTRY.
    """

    validation_schema = SCHEMA_REGISTRY.get(UploadTables(table_name))
    if validation_schema is None:
        raise ValueError(f"No validation schema found for table: {table_name}")

    validated: list[UploadRow] = []
    errors: list[dict] = []
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
        raise UploadValidationError(failed_rows=failed_rows, errors=errors)
    return validated
