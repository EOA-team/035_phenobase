from enum import StrEnum


class Role(StrEnum):
    """Currently supported user roles."""

    admin = "admin"
    reader = "reader"
    writer = "writer"
class Status(StrEnum):
    """Currently supported user statuses."""

    active = "active"
    inactive = "inactive"