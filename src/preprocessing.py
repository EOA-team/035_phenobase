import pandas as pd

from src.models.tables.user import User


def _normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase headers and strip surrounding whitespace."""
    df = df.copy()
    df.columns = df.columns.str.lower()  # Lower on headers
    df.columns = df.columns.str.strip()  # Strip whitespace on headers
    return df


def _strip_whitespace_from_values(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from values(e.g. modes " insert" or "update " instead of "insert" or "update").
    Note: ' ' is accepted"""
    return df.map(lambda x: x.strip() if isinstance(x, str) else x)


def _lowercase_mode(df: pd.DataFrame) -> pd.DataFrame:
    """Make sure "Insert" or "Update" is treated the same as "insert" or "update"."""
    df = df.copy()
    if "mode" in df.columns:
        df["mode"] = df["mode"].str.lower()  # Lower on modes
    return df


def _sanitize_null_values(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize all Pandas Null values (pd.NA, np.nan) to None for consistency."""
    mask = df.notna()
    new_df = df.astype(object).where(mask, None)  # Replace NaN with None
    return new_df


def _clean_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Basic cleaning of an uploaded DataFrame."""
    df = _normalize_headers(raw_df)
    df = _strip_whitespace_from_values(df)
    df = _lowercase_mode(df)
    return _sanitize_null_values(df)


def _add_data_lineage(df: pd.DataFrame, user: User) -> pd.DataFrame:
    """Append user IDs to the DataFrame based on the table name.
    The pydantic row models will use creator_id on insert and updater_id on update, so we add both here."""
    df["creator_id"] = user.id  # required for insert model
    df["updater_id"] = user.id  # required for update model
    df["user"] = (
        user.firstname + " " + user.lastname
    )  # optional information for debugging
    return df


def prepare_dataframe(parsed_df: pd.DataFrame, user: User) -> pd.DataFrame:
    """Prepare Daframe for pydanrtic validation"""
    df = _clean_dataframe(parsed_df)
    df = _add_data_lineage(df, user)
    return df
