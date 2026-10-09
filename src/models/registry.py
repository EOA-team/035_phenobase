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
from src.models.tables.plot import (
    Plot,
    PlotBase,
)
from src.models.tables.plot_collection import (
    PlotCollection,
    PlotCollectionBase,
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


class CsvTables(StrEnum):
    """Tables uploadable as row-shaped CSV via /data/upload/csv/{table_name}."""

    CROP_TYPE = "crop_type"
    TREATMENT = "treatment"
    UNIT = "unit"
    VARIABLE = "variable"
    USER = "user"


class GeojsonTables(StrEnum):
    """Aggregate tables owning one upload file each via /data/upload/geojson/{table_name}."""

    PLOT_COLLECTION = "plot_collection"


class DerivedTables(StrEnum):
    """Tables with no upload identity of their own; populated exclusively via another table's file."""

    PLOT = "plot"


class ManagedTables(StrEnum):
    """Tables managed by the Phenobase API."""

    CROP_TYPE = CsvTables.CROP_TYPE.value
    TREATMENT = CsvTables.TREATMENT.value
    UNIT = CsvTables.UNIT.value
    VARIABLE = CsvTables.VARIABLE.value
    USER = CsvTables.USER.value
    PLOT_COLLECTION = GeojsonTables.PLOT_COLLECTION.value
    PLOT = DerivedTables.PLOT.value


@dataclass(frozen=True)
class TableSchema:
    """Configuration for one API-managed table.

    base_model:   SQL Base Model , all other models are derived from this.
    row_model:    A row model defined in src.models.row_models, used to validate uploaded records for this table.
                  Type is resolved during runtime via the ``mode`` field, which discriminates between Insert, Update, and Delete variants.
                  ``None`` marks tables without row models: (e.g. plots which are derived from plot_collection)
    table_model:  SQLModel class (declared with table=True) the validated records
                  are written to.
    read_model:   SQLModel class used as the API response model for reading this
                  table.
    read_order:   Optional explicit column order for reading this table. If None,
                  the model's natural field order is used.
    filetype:     File format the API accepts for this table; ``None`` for derived
                  tables (e.g. plots) .
    """

    base_model: type[BaseModel]
    # Only select row_models from the row_models.py file despite type is Any
    # Needed to select Any, because Static Type checking via Mypy is not possible here, as the row_model is defined during runtime.
    row_model: Any
    table_model: type[SQLModel]
    read_model: type[SQLModel]
    filetype: UploadFileType | None = None
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
SCHEMA_REGISTRY: dict[ManagedTables, TableSchema] = {
    ManagedTables.CROP_TYPE: TableSchema(
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
    ManagedTables.TREATMENT: TableSchema(
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
    ManagedTables.UNIT: TableSchema(
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
    ManagedTables.VARIABLE: TableSchema(
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
    ManagedTables.USER: TableSchema(
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
    ManagedTables.PLOT_COLLECTION: TableSchema(
        base_model=PlotCollectionBase,
        row_model=None,
        table_model=PlotCollection,
        read_model=PlotCollection,
        filetype=UploadFileType.GEOJSON,
        read_order=[
            "id",
            "name",
            "category",
            "crs",
            "creator_id",
            "created_at",
            "updater_id",
            "updated_at",
        ],
    ),
    ManagedTables.PLOT: TableSchema(
        base_model=PlotBase,
        row_model=None,
        table_model=Plot,
        read_model=Plot,
        read_order=[
            "id",
            "plot_collection_id",
            "label",
            "row",
            "col",
            "creator_id",
            "created_at",
            "updater_id",
            "updated_at",
            "geometry",
        ],
    ),
}
