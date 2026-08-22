from datetime import datetime, UTC


def utc_now() -> datetime:
    """Get the current UTC time."""
    return datetime.now(tz=UTC)