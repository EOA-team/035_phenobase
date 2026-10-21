from fastapi import HTTPException, UploadFile

from src.models.registry import (
    SCHEMA_REGISTRY,
    UploadTables,
)


def validate_uploaded_file(table_name: UploadTables, upload_file: UploadFile) -> None:
    """Validate the input file for uploading to the Data Platform."""
    schema = SCHEMA_REGISTRY.get(table_name)
    if schema is None:
        raise HTTPException(
            status_code=400, detail=f"Unsupported table for upload: {table_name}"
        )
    if upload_file.filename is None:
        raise HTTPException(
            status_code=400, detail="Missing filename in the uploaded file."
        )
    filetype = upload_file.filename.split(".")[-1]
    if not upload_file.filename.endswith(str(schema.filetype.value)):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format *.{filetype} for table '{table_name}'. "
            f"Supported file format: *.{schema.filetype.value}",
        )


def build_upload_csv_template(table_name: UploadTables) -> str:
    """Generates a csv template for data upload on the given table_name,
    based on the base model in SCHEMA_REGISTRY."""

    validation_schema = SCHEMA_REGISTRY.get(UploadTables(table_name))
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
