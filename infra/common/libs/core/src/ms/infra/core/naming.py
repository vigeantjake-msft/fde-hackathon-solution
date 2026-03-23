"""Resource naming utilities for Azure infrastructure."""

import hashlib
import re


def sanitize_for_resource_name(value: str) -> str:
    """Sanitize a string for use in Azure resource names.

    Replaces characters that are invalid in resource names with hyphens.
    Valid characters are letters, numbers, and hyphens.
    e.g., "user@example.com" -> "user-example-com", "my_resource.name" -> "my-resource-name"
    """
    return re.sub(r"[^a-zA-Z0-9-]", "-", value)


def sanitize_to_lowercase_alphanumeric(value: str) -> str:
    """Sanitize a string to lowercase alphanumeric characters only.

    Removes all non-alphanumeric characters and converts to lowercase.
    This is required for Azure resources with strict naming constraints like Storage Accounts.

    Args:
        value: The string to sanitize.

    Returns:
        String containing only lowercase letters and numbers.

    Example:
        >>> sanitize_to_lowercase_alphanumeric("My_App-Name!")
        'myappname'
    """
    return "".join(c for c in value if c.isalnum()).lower()


def _project_tag(project_name: str) -> str:
    """Extract first three alphanumeric chars of the project name.

    Used as a short identifier in resource names with strict length constraints.
    """
    sanitized = sanitize_to_lowercase_alphanumeric(project_name)
    return sanitized[:3]


def _stack_tag(stack_name: str) -> str:
    """Generate up-to-4-char tag from stack name.

    Pattern: first 3 chars + last char of stack identifier.

    Args:
        stack_name: The stack name to process.

    Returns:
        A 1-4 character tag representing the stack.
    """
    base = sanitize_to_lowercase_alphanumeric(stack_name)

    first_three = base[:3]
    last_char = base[-1:] if len(base) > 3 else ""
    return f"{first_three}{last_char}" or base


def generate_storage_account_name(
    *,
    project_name: str,
    stack_name: str,
    app_name: str,
    subscription_id: str,
) -> str:
    """Generate deterministic storage account name satisfying Azure's constraints.

    Azure Storage Account naming requirements:
    - 3-24 characters in length
    - Lowercase letters and numbers only
    - Globally unique across all Azure

    Pattern: st{projecttag}{stacktag}{appsegment}{hashsuffix}
    - prefix "st" for "storage" (2 chars)
    - projecttag: first 3 alphanumeric chars of project name (3 chars)
    - stacktag: up to 4 chars from stack name (4 chars)
    - appsegment: first 9 alphanumeric chars of app name (9 chars)
    - hashsuffix: 6-char hash for uniqueness (6 chars)
    Total: 2 + 3 + 4 + 9 + 6 = 24 chars

    The hash ensures global uniqueness even if the human-readable segments collide.
    The name is deterministic - same inputs always produce the same output.

    Args:
        project_name: Pulumi project name.
        stack_name: Pulumi stack name.
        app_name: Application identifier.
        subscription_id: Azure subscription ID. Included in the hash to ensure uniqueness across subscriptions.

    Returns:
        A valid, deterministic storage account name.

    Example:
        >>> generate_storage_account_name(
        ...     project_name="fde",
        ...     stack_name="dev-alice",
        ...     app_name="sample-app",
        ...     subscription_id="00000000-0000-0000-0000-000000000000",
        ... )
        'stfdealisampleapp123abc'
    """
    project_segment = _project_tag(project_name)
    stack_segment = _stack_tag(stack_name)
    app_segment = sanitize_to_lowercase_alphanumeric(app_name)[:9]

    # Generate hash for uniqueness
    hash_input = "|".join([project_name, stack_name, app_name, subscription_id])
    hash_suffix = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:6]

    name = f"st{project_segment}{stack_segment}{app_segment}{hash_suffix}"

    return name
