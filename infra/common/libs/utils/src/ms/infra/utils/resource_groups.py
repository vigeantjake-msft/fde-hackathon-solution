import pulumi
from pulumi_azure_native import resources


def get_and_protect_existing_resource_group(name: str) -> resources.ResourceGroup:
    """
    Get an existing resource group by name, and protect it from deletion.

    This is typically used when a customer has already created a resource group
    manually for us to use outside of Pulumi.
    """
    return resources.ResourceGroup.get(
        "rg",
        id=resources.get_resource_group(name).id,
        opts=pulumi.ResourceOptions(
            protect=True,
            retain_on_delete=True,
        ),
    )
