import pandas as pd
from pydantic import TypeAdapter, ValidationError

from src.models.registry import (
    SCHEMA_REGISTRY,
    UploadTables,
)
from src.models.row_models import UploadRow


class UploadValidationError(Exception):
    def __init__(self, total_entries: int, errors: list[dict], max_shown: int = 20):
        self.total_entries = total_entries
        self.errors = errors
        self.failed_entries = len({e["index"] for e in errors})

        lines = [f"{self.failed_entries} of {total_entries} entries are invalid:"]
        for e in errors[:max_shown]:
            lines.append(
                f"  - index {e['index']}, column '{e['column']}': {e['message']} (got {e['value']!r})"
            )
        if len(errors) > max_shown:
            lines.append(f"  ... and {len(errors) - max_shown} more errors")

        super().__init__("\n".join(lines))


def validate_file_content(
    df: pd.DataFrame, table_name: UploadTables
) -> list[UploadRow]:
    schema = SCHEMA_REGISTRY.get(UploadTables(table_name))
    if schema is None:
        raise ValueError(f"No validation schema found for table: {table_name}")

    adapter = TypeAdapter(schema.row_model)
    validated, errors = [], []

    for index, record in zip(df.index, df.to_dict(orient="records"), strict=True):
        try:
            validated.append(adapter.validate_python(record))
        except ValidationError as exc:
            for err in exc.errors(include_url=False, include_context=False):
                errors.append(
                    {
                        "index": index,
                        "column": ".".join(map(str, err["loc"])),
                        "message": err["msg"],
                        "value": str(err.get("input")),
                    }
                )

    if errors:
        raise UploadValidationError(len(df), errors)
    return validated
