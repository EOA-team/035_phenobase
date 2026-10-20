import pandas as pd
from fastapi import UploadFile


def parse_csv(upload_file: UploadFile) -> pd.DataFrame:
    """Parse the uploaded CSV file into a pandas DataFrame."""
    upload_file.file.seek(0)
    try:
        df = pd.read_csv(
            upload_file.file,
            sep=None,  # Pandas auto sniffs the separator
            engine="python",
            encoding="utf-8-sig",  # automatically remove Excel BOM artifacts safely
        )
        return df
    except ValueError as e:
        raise ValueError(f"Failed to read CSV file: {e}") from e
