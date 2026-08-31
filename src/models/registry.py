"""Registry of all tables , here new tables can be added to the registry and the API will automatically support them."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from pydantic import BaseModel
from sqlmodel import SQLModel

from src.models.base import UploadFileType
from src.models.row_models import (
    CropTypeRow,
    TreatmentRow,
    UnitRow,
    UserRow,
    VariableRow,
)
from src.models.tables.crop_type import (
    CropType,
    CropTypeBase,
)
from src.models.tables.treatment import (
    Treatment,
    TreatmentBase,
)
from src.models.tables.unit import (
    Unit,
    UnitBase,
)
from src.models.tables.user import (
    User,
)
from src.models.tables.variable import (
    Variable,
    VariableBase,
)


class UploadTables(StrEnum):
    """Tables managed by the Phenobase API."""

    CROP_TYPE = "crop_type"
    TREATMENT = "treatment"
    UNIT = "unit"
    VARIABLE = "variable"
    USER = "user"
    ###Add here more


@dataclass(frozen=True)
class TableSchema:
    """Configuration for one API-managed table.

    base_model:   SQL Base Model , all other models are derived from this.
    row_model:    A row model defined in src.models.row_models, used to validate uploaded records for this table.
                  Type is resolved during runtime via the ``mode`` field, which discriminates between Insert, Update, and Delete variants.
    table_model:  SQLModel class (declared with table=True) the validated records
                  are written to.
    read_model:   SQLModel class used as the API response model for reading this
                  table.
    read_order:   Optional explicit column order for reading this table. If None,
                  the model's natural field order is used.
    filetype:     File format the API accepts for this table.
    """

    base_model: type[BaseModel]
    # Only select row_models from the row_models.py file despite type is Any
    # Needed to select Any, because Static Type checking via Mypy is not possible here, as the row_model is defined during runtime.
    row_model: Any
    table_model: type[SQLModel]
    read_model: type[SQLModel]
    filetype: UploadFileType
    read_order: list[str] | None = None

    def __post_init__(self) -> None:
        # SQLAlchemy attaches __table__ only to classes declared with table=True,
        # so this guards against accidentally registering a non-table model.
        if getattr(self.table_model, "__table__", None) is None:
            raise TypeError(
                f"{self.table_model.__name__} is not a SQLModel table "
                f"(missing table=True / __table__)."
            )


# Configuration for each API-managed table: row model(s), target table, read model,
# and accepted filetype.
SCHEMA_REGISTRY: dict[UploadTables, TableSchema] = {
    UploadTables.CROP_TYPE: TableSchema(
        base_model=CropTypeBase,
        row_model=CropTypeRow,
        table_model=CropType,
        read_model=CropType,
        filetype=UploadFileType.CSV,
        read_order=[
            "id",
            "name",
            "code",
            "description",
            "creator_id",
            "created_at",
            "updater_id",
            "updated_at",
            "doc_path",
        ],
    ),
    UploadTables.TREATMENT: TableSchema(
        base_model=TreatmentBase,
        row_model=TreatmentRow,
        table_model=Treatment,
        read_model=Treatment,
        filetype=UploadFileType.CSV,
        read_order=[
            "id",
            "name",
            "code",
            "description",
            "creator_id",
            "created_at",
            "updater_id",
            "updated_at",
            "doc_path",
        ],
    ),
    UploadTables.UNIT: TableSchema(
        base_model=UnitBase,
        row_model=UnitRow,
        table_model=Unit,
        read_model=Unit,
        filetype=UploadFileType.CSV,
        read_order=[
            "id",
            "name",
            "code",
            "description",
            "creator_id",
            "created_at",
            "updater_id",
            "updated_at",
        ],
    ),
    UploadTables.VARIABLE: TableSchema(
        base_model=VariableBase,
        row_model=VariableRow,
        table_model=Variable,
        read_model=Variable,
        filetype=UploadFileType.CSV,
        read_order=[
            "id",
            "name",
            "code",
            "description",
            "creator_id",
            "created_at",
            "updater_id",
            "updated_at",
        ],
    ),
    UploadTables.USER: TableSchema(
        base_model=User,
        row_model=UserRow,
        table_model=User,
        read_model=User,
        filetype=UploadFileType.CSV,
        read_order=[
            "id",
            "f_account",
            "firstname",
            "lastname",
            "status",
            "role",
            "email",
        ],
    ),
}
