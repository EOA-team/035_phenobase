"""Insert/Update/Delete row-model unions for each table accessed via API.

Each ``*Row`` type alias is the discriminated union used to validate one uploaded
record: pydantic uses ``mode`` to choose the Insert, Update, or Delete variant during runtime.
"""

from typing import Annotated

from pydantic import Field

from src.models.tables.crop_type import (
    CropTypeDelete,
    CropTypeInsert,
    CropTypeUpdate,
)
from src.models.tables.treatment import (
    TreatmentDelete,
    TreatmentInsert,
    TreatmentUpdate,
)
from src.models.tables.unit import (
    UnitDelete,
    UnitInsert,
    UnitUpdate,
)
from src.models.tables.user import (
    UserDelete,
    UserInsert,
    UserUpdate,
)
from src.models.tables.variable import (
    VariableDelete,
    VariableInsert,
    VariableUpdate,
)

type CropTypeRow = Annotated[
    CropTypeInsert | CropTypeUpdate | CropTypeDelete,
    Field(discriminator="mode"),
]
type TreatmentRow = Annotated[
    TreatmentInsert | TreatmentUpdate | TreatmentDelete,
    Field(discriminator="mode"),
]
type UnitRow = Annotated[
    UnitInsert | UnitUpdate | UnitDelete,
    Field(discriminator="mode"),
]
type VariableRow = Annotated[
    VariableInsert | VariableUpdate | VariableDelete,
    Field(discriminator="mode"),
]
type UserRow = Annotated[
    UserInsert | UserUpdate | UserDelete,
    Field(discriminator="mode"),
]
