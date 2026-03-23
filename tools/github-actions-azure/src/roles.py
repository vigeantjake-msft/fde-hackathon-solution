from enum import StrEnum

from src.settings import settings


class BuiltInRole(StrEnum):
    # Allows for read, write and delete access to Azure Storage blob containers and data.
    STORAGE_BLOB_DATA_CONTRIBUTOR = "ba92f5b4-2d11-453d-a403-e96b0029c9fe"

    def to_definition_id(self) -> str:
        return "/".join(
            [
                "",
                "subscriptions",
                settings.subscription_id,
                "providers",
                "Microsoft.Authorization",
                "roleDefinitions",
                self.value,
            ]
        )
