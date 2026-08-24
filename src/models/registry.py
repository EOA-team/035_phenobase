"""Registry of all tables , here new tables can be added to the registry and the API will automatically support them."""

from dataclasses import dataclass
from enum import StrEnum
from types import UnionType

from pydantic import BaseModel
from sqlmodel import SQLModel

from src.models.base import UploadFileType
from src.models.tables.crop_type import (
    CropType,
    CropTypeDelete,
    CropTypeInsert,
    CropTypeUpdate,
)
from src.models.tables.treatment import (
    Treatment,
    TreatmentDelete,
    TreatmentInsert,
    TreatmentUpdate,
)  

from src.models.tables.unit import (
    Unit,
    UnitDelete,
    UnitInsert,
    UnitUpdate,  
)

from src.models.tables. variable import (
    Variable,
    VariableDelete,
    VariableInsert,
    VariableUpdate,
)



class UploadTables(StrEnum):
    """Tables managed by the Phenobase API."""

    CROP_TYPE = "crop_type"
    TREATMENT = "treatment"
    UNIT = "unit"
    VARIABLE = "variable"
    ###Add here more 


@dataclass(frozen=True)
class TableSchema:
    """Configuration for one API-managed table.

    row_model:    Pydantic Basemodel (or union of insert/update/delete models) used to
                  validate each uploaded record.
    table_model:  SQLModel class (declared with table=True) the validated records
                  are written to.
    read_model:   SQLModel class used as the API response model for reading this
                  table.
    read_order:   Optional explicit column order for reading this table. If None,
                  the model's natural field order is used.
    filetype:     File format the API accepts for this table.
    """

    row_model: type[BaseModel] | UnionType
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
        row_model=CropTypeInsert | CropTypeUpdate | CropTypeDelete,
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
        row_model=TreatmentInsert | TreatmentUpdate | TreatmentDelete,
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
        row_model=UnitInsert | UnitUpdate | UnitDelete,
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
        row_model=VariableInsert | VariableUpdate | VariableDelete,
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
}
