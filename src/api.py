from enum import StrEnum


class Role(StrEnum):
    """Currently supported user roles."""
    admin = "admin"
    reader = "reader"
    writer = "writer"
