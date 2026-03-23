from enum import StrEnum

from ms.infra.core.settings import settings


class BuiltInRole(StrEnum):
    # View all resources, but does not allow you to make any changes.
    READER = "acdd72a7-3385-48ef-bd42-f606fba81ae7"

    # Grants full access to manage all resources, but does not allow assigning roles
    # in Azure RBAC, manage assignments in Azure Blueprints, or share image galleries.
    CONTRIBUTOR = "b24988ac-6180-42a0-ab88-20f7382dd24c"

    # Manage access to Azure resources by assigning roles using Azure RBAC.
    # This role does not allow managing access using other ways, such as Azure Policy.
    RBAC_ADMINISTRATOR = "f58310d9-a9f6-439a-9e8d-f62e7b41a168"

    # Allows for read, write and delete access to Azure Storage blob containers and data.
    STORAGE_BLOB_DATA_CONTRIBUTOR = "ba92f5b4-2d11-453d-a403-e96b0029c9fe"

    # Allows for read access to Azure Storage blob containers and data.
    STORAGE_BLOB_DATA_READER = "2a2b9908-6ea1-4ae2-8e65-a410df84e7d1"

    # Allows for read, write and delete access to Azure Storage queue data.
    STORAGE_QUEUE_DATA_CONTRIBUTOR = "974c5e8b-45b9-4653-ba55-5f855dd0fb88"

    # Allows for read, write and delete access to Azure Storage table data.
    STORAGE_TABLE_DATA_CONTRIBUTOR = "0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3"

    # Ability to view files, models, deployments. Readers can't make any changes.
    # They can inference and create images.
    COGNITIVE_SERVICES_OPENAI_USER = "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd"

    # Full access to all Cognitive Services (OpenAI, Content Understanding, Document Intelligence, Vision, etc.)
    COGNITIVE_SERVICES_USER = "a97b65f3-24c7-4388-baec-2e87135dc908"

    # Can perform all actions within an Azure AI resource besides managing the resource itself.
    AZURE_AI_DEVELOPER = "64702f94-c441-49e6-a78b-ef80e0188fee"

    # Push container images to a container registry.
    ACR_PUSH = "8311e382-0749-4cb8-b61a-304f252e45ec"

    # Pull container images from a container registry.
    ACR_PULL = "7f951dda-4ed3-4680-a7ca-43fe172d538d"

    # Perform any action on Key Vault secrets (get, set, delete, list, etc.)
    KEY_VAULT_SECRETS_OFFICER = "b86a8fe4-44ce-4948-aee5-eccb2c155cd7"

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
