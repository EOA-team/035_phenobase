"""Insert/Update/Delete upload-model unions for each table accessed via API.

Each type alias (suffix ``Upload``) is the discriminated union used to validate
one uploaded record: pydantic uses ``mode`` to choose the Insert, Update, or
Delete variant during runtime. CSV pipelines validate one record per file row;
the GeoJSON header union validates the collection-level record of a plot
collection upload, the plot union validates one row per plot/feature.
"""

from typing import Annotated

from pydantic import Field

from src.models.tables.crop_type import (
    CropTypeDelete,
    CropTypeInsert,
    CropTypeUpdate,
)
from src.models.tables.plot import (
    PlotDelete,
    PlotInsert,
    PlotUpdate,
)
from src.models.tables.plot_collection import (
    PlotCollectionDelete,
    PlotCollectionInsert,
    PlotCollectionUpdate,
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

type CropTypeUpload = Annotated[
    CropTypeInsert | CropTypeUpdate | CropTypeDelete,
    Field(discriminator="mode"),
]
type TreatmentUpload = Annotated[
    TreatmentInsert | TreatmentUpdate | TreatmentDelete,
    Field(discriminator="mode"),
]
type UnitUpload = Annotated[
    UnitInsert | UnitUpdate | UnitDelete,
    Field(discriminator="mode"),
]
type VariableUpload = Annotated[
    VariableInsert | VariableUpdate | VariableDelete,
    Field(discriminator="mode"),
]
type UserUpload = Annotated[
    UserInsert | UserUpdate | UserDelete,
    Field(discriminator="mode"),
]
type PlotCollectionUpload = Annotated[
    PlotCollectionInsert | PlotCollectionUpdate | PlotCollectionDelete,
    Field(discriminator="mode"),
]
type PlotUpload = Annotated[
    PlotInsert | PlotUpdate | PlotDelete,
    Field(discriminator="mode"),
]
