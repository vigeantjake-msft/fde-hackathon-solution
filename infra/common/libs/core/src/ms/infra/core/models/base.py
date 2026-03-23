from pydantic import BaseModel  # noqa: TID251 # need to import BaseModel to define FrozenBaseModel
from pydantic import ConfigDict


class FrozenBaseModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,
    )
