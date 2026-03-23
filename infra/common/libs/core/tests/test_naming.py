import pytest

from ms.infra.core.naming import generate_storage_account_name
from ms.infra.core.naming import sanitize_for_resource_name


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(
            "simple",
            "simple",
            id="simple alphanumeric unchanged",
        ),
        pytest.param(
            "with-hyphens",
            "with-hyphens",
            id="hyphens preserved",
        ),
        pytest.param(
            "user@example.com",
            "user-example-com",
            id="email address",
        ),
        pytest.param(
            "user_name",
            "user-name",
            id="underscores replaced",
        ),
        pytest.param(
            "my.resource.name",
            "my-resource-name",
            id="dots replaced",
        ),
        pytest.param(
            "name with spaces",
            "name-with-spaces",
            id="spaces replaced",
        ),
        pytest.param(
            "MixedCase123",
            "MixedCase123",
            id="mixed case and numbers preserved",
        ),
        pytest.param(
            "special!@#$%chars",
            "special-----chars",
            id="special characters replaced",
        ),
        pytest.param(
            "user@contoso.onmicrosoft.com",
            "user-contoso-onmicrosoft-com",
            id="UPN format",
        ),
        pytest.param(
            "first.last@domain.com",
            "first-last-domain-com",
            id="UPN with dots in local part",
        ),
        pytest.param(
            "a__b..c@@d",
            "a--b--c--d",
            id="consecutive special chars become consecutive hyphens",
        ),
        pytest.param(
            "",
            "",
            id="empty string",
        ),
    ],
)
def test_sanitize_for_resource_name_returns_expected(
    value: str,
    expected: str,
) -> None:
    result = sanitize_for_resource_name(value)

    assert result == expected


@pytest.mark.parametrize(
    ("project", "stack", "app_name", "subscription_id"),
    [
        pytest.param("fde", "fbujaroski", "sample-durable-function", "sub-a", id="typical stack"),
        pytest.param("p", "a", "x", "sub-b", id="short inputs"),
        pytest.param(
            "very-long-project", "very-long-username", "very-long-app-name", "subscription-id-c", id="long inputs"
        ),
    ],
)
def test_generate_storage_account_name_meets_azure_constraints(
    project: str,
    stack: str,
    app_name: str,
    subscription_id: str,
) -> None:
    result = generate_storage_account_name(
        project_name=project,
        stack_name=stack,
        app_name=app_name,
        subscription_id=subscription_id,
    )

    assert 3 <= len(result) <= 24
    assert result.isalnum()
    assert result.islower()
    assert result.startswith("st")


@pytest.mark.parametrize(
    ("project", "stack", "app_name", "subscription_id", "expected_prefix"),
    [
        pytest.param(
            "fde",
            "fbujaroski",
            "sample-durable-function",
            "sub-a",
            "stfdefbuisampledur",
            id="dev stack readable prefix",
        ),
        pytest.param(
            "My Project!!",
            "__A__B__",
            "Durable Function!!!",
            "sub-b",
            "stmypabdurablefu",
            id="sanitizes special chars",
        ),
        pytest.param(
            "ABC",
            "staging!!**",
            "APP",
            "sub-c",
            "stabcstagapp",
            id="non-dev stack",
        ),
        pytest.param(
            "x",
            "y",
            "z",
            "sub-d",
            "stxyz",
            id="minimal inputs",
        ),
    ],
)
def test_generate_storage_account_name_builds_expected_segments(
    project: str,
    stack: str,
    app_name: str,
    subscription_id: str,
    expected_prefix: str,
) -> None:
    result = generate_storage_account_name(
        project_name=project,
        stack_name=stack,
        app_name=app_name,
        subscription_id=subscription_id,
    )

    assert result.startswith(expected_prefix)
    assert len(result) == len(expected_prefix) + 6


@pytest.mark.parametrize(
    ("inputs_a", "inputs_b", "expect_equal"),
    [
        pytest.param(
            {"project_name": "fde", "stack_name": "test", "app_name": "sample", "subscription_id": "sub-a"},
            {"project_name": "fde", "stack_name": "test", "app_name": "sample", "subscription_id": "sub-a"},
            True,
            id="identical inputs deterministic",
        ),
        pytest.param(
            {"project_name": "fde", "stack_name": "alice", "app_name": "sample", "subscription_id": "sub-a"},
            {"project_name": "fde", "stack_name": "staging", "app_name": "sample", "subscription_id": "sub-a"},
            False,
            id="different stacks",
        ),
        pytest.param(
            {"project_name": "fde", "stack_name": "test", "app_name": "sample", "subscription_id": "sub-a"},
            {"project_name": "fde", "stack_name": "test", "app_name": "other", "subscription_id": "sub-a"},
            False,
            id="different apps",
        ),
        pytest.param(
            {"project_name": "fde", "stack_name": "test", "app_name": "sample", "subscription_id": "sub-a"},
            {"project_name": "abc", "stack_name": "test", "app_name": "sample", "subscription_id": "sub-a"},
            False,
            id="different projects",
        ),
        pytest.param(
            {"project_name": "fde", "stack_name": "test", "app_name": "sample", "subscription_id": "sub-a"},
            {"project_name": "fde", "stack_name": "test", "app_name": "sample", "subscription_id": "sub-b"},
            False,
            id="different subscriptions",
        ),
    ],
)
def test_generate_storage_account_name_equality_rules(
    inputs_a: dict[str, str],
    inputs_b: dict[str, str],
    expect_equal: bool,
) -> None:
    name_a = generate_storage_account_name(**inputs_a)
    name_b = generate_storage_account_name(**inputs_b)

    assert (name_a == name_b) is expect_equal
