from datetime import UTC, datetime


def utc_now() -> datetime:
    """Get the current UTC time."""
    return datetime.now(tz=UTC)
