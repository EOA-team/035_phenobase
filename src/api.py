from enum import StrEnum


class Role(StrEnum):
    """Currently supported user roles."""

    reader = "reader"
    writer = "writer"
