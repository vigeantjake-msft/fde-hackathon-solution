from pydantic import Field

from ms.infra.core.models.base import FrozenBaseModel


class EasyAuthConfig(FrozenBaseModel):
    easy_auth_app_client_id: str | None = Field(
        default=None,
        min_length=1,
        description="Pre-existing Entra app registration client ID. "
        "If omitted, the code auto-creates a registration (requires Application.ReadWrite.All).",
    )

    # This only configures application access, not user access
    # Empty lists are allowed - this is useful for scenarios where no applications are allowed access
    allowed_app_client_ids: list[str]
