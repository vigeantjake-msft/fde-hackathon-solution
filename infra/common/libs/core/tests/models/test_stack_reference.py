import uuid
from typing import Any

import pulumi
import pytest
from pydantic import ValidationError

MOCK_STACK_OUTPUTS: dict[str, Any] = {
    "_export_resource_group_name": "my-rg",
    "_export_vnet_id": "/subscriptions/abc/vnet/my-vnet",
    "_export_single_field": "value",
    "_export_name": "my-resource",
    "_export_description": None,
}


class MyMocks(pulumi.runtime.Mocks):
    def new_resource(
        self,
        args: pulumi.runtime.MockResourceArgs,
    ):
        outputs: dict[Any, Any] = {**args.inputs}

        if args.typ == "pulumi:pulumi:StackReference":
            outputs["outputs"] = MOCK_STACK_OUTPUTS

        outputs["id"] = str(uuid.uuid4())
        outputs["name"] = args.name

        return args.name + "_id", outputs

    def call(
        self,
        args: pulumi.runtime.MockCallArgs,
    ):
        return {}


pulumi.runtime.set_mocks(MyMocks())

from ms.infra.core.models.stack_reference import (  # noqa: E402 # imports need to be after mocks are set
    StackOutputBaseModel,
)


class SampleOutputs(StackOutputBaseModel):
    resource_group_name: str
    vnet_id: str
    optional_tag: str | None = None


class MinimalOutputs(StackOutputBaseModel):
    single_field: str


class NullableRequiredOutputs(StackOutputBaseModel):
    name: str
    description: str | None  # required but nullable


# --- Consumer: from_stack_reference ---


@pulumi.runtime.test
def test_from_stack_reference_resolves_valid_outputs() -> None:
    """Valid outputs from a StackReference resolve to a validated model."""
    ref = pulumi.StackReference("organization/project/stack")
    result = SampleOutputs.from_stack_reference(ref)

    def _assert(model: SampleOutputs) -> None:
        assert isinstance(model, SampleOutputs)
        assert model.resource_group_name == "my-rg"
        assert model.vnet_id == "/subscriptions/abc/vnet/my-vnet"
        assert model.optional_tag is None

    result.apply(_assert)


@pulumi.runtime.test
def test_from_stack_reference_minimal_model() -> None:
    """A model with a single field resolves correctly."""
    ref = pulumi.StackReference("organization/project/stack")
    result = MinimalOutputs.from_stack_reference(ref)

    def _assert(model: MinimalOutputs) -> None:
        assert isinstance(model, MinimalOutputs)
        assert model.single_field == "value"

    result.apply(_assert)


@pulumi.runtime.test
def test_from_stack_reference_nullable_required_field() -> None:
    """Required-but-nullable fields (str | None) resolve correctly when None."""
    ref = pulumi.StackReference("organization/project/stack")
    result = NullableRequiredOutputs.from_stack_reference(ref)

    def _assert(model: NullableRequiredOutputs) -> None:
        assert isinstance(model, NullableRequiredOutputs)
        assert model.name == "my-resource"
        assert model.description is None

    result.apply(_assert)


# --- Producer: export_outputs ---


def test_export_outputs_with_valid_plain_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Plain values matching the schema are exported with _export_ prefix."""
    exported: dict[str, Any] = {}
    monkeypatch.setattr(pulumi, "export", lambda name, value: exported.update({name: value}))

    SampleOutputs.export_outputs(
        resource_group_name="my-rg",
        vnet_id="/subscriptions/.../vnet",
        optional_tag="v1",
    )

    assert exported == {
        "_export_resource_group_name": "my-rg",
        "_export_vnet_id": "/subscriptions/.../vnet",
        "_export_optional_tag": "v1",
    }


def test_export_outputs_includes_none_optional_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """Optional fields can be explicitly set to None."""
    exported: dict[str, Any] = {}
    monkeypatch.setattr(pulumi, "export", lambda name, value: exported.update({name: value}))

    SampleOutputs.export_outputs(
        resource_group_name="my-rg",
        vnet_id="/subscriptions/.../vnet",
        optional_tag=None,
    )

    assert exported["_export_optional_tag"] is None


def test_export_outputs_rejects_missing_keys() -> None:
    """Missing required fields raise TypeError."""
    with pytest.raises(TypeError, match="Missing outputs"):
        SampleOutputs.export_outputs(resource_group_name="my-rg")


def test_export_outputs_rejects_extra_keys() -> None:
    """Unknown fields raise TypeError."""
    with pytest.raises(TypeError, match="Unexpected outputs"):
        SampleOutputs.export_outputs(
            resource_group_name="my-rg",
            vnet_id="id",
            optional_tag=None,
            unknown_field="bad",
        )


def test_export_outputs_validates_plain_value_types() -> None:
    """Plain values with wrong types are rejected immediately."""
    with pytest.raises(ValidationError):
        SampleOutputs.export_outputs(
            resource_group_name=123,  # should be str
            vnet_id="ok",
            optional_tag=None,
        )


@pulumi.runtime.test
def test_export_outputs_with_output_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Output values are validated when they resolve and exported with _export_ prefix."""
    exported: dict[str, Any] = {}
    monkeypatch.setattr(pulumi, "export", lambda name, value: exported.update({name: value}))

    MinimalOutputs.export_outputs(
        single_field=pulumi.Output.from_input("hello"),
    )

    # The exported key should be prefixed
    assert "_export_single_field" in exported
    assert isinstance(exported["_export_single_field"], pulumi.Output)

    def _assert(value: str) -> None:
        assert value == "hello"

    exported["_export_single_field"].apply(_assert)


def test_export_outputs_minimal_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """A model with a single field works correctly."""
    exported: dict[str, Any] = {}
    monkeypatch.setattr(pulumi, "export", lambda name, value: exported.update({name: value}))

    MinimalOutputs.export_outputs(single_field="value")

    assert exported == {"_export_single_field": "value"}


def test_export_outputs_nullable_required_with_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """Required-but-nullable field accepts a string value."""
    exported: dict[str, Any] = {}
    monkeypatch.setattr(pulumi, "export", lambda name, value: exported.update({name: value}))

    NullableRequiredOutputs.export_outputs(name="my-resource", description="some desc")

    assert exported["_export_description"] == "some desc"


def test_export_outputs_nullable_required_with_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Required-but-nullable field accepts None."""
    exported: dict[str, Any] = {}
    monkeypatch.setattr(pulumi, "export", lambda name, value: exported.update({name: value}))

    NullableRequiredOutputs.export_outputs(name="my-resource", description=None)

    assert exported["_export_description"] is None


def test_export_outputs_nullable_required_missing() -> None:
    """Required-but-nullable field must still be provided."""
    with pytest.raises(TypeError, match="Missing outputs"):
        NullableRequiredOutputs.export_outputs(name="my-resource")


# --- Model validation ---


def test_model_is_frozen() -> None:
    """StackOutputBaseModel instances are immutable."""
    outputs = SampleOutputs(
        resource_group_name="my-rg",
        vnet_id="/subscriptions/.../vnet",
    )

    with pytest.raises(ValidationError):
        outputs.resource_group_name = "other-rg"  # type: ignore[misc]


def test_model_validation_rejects_missing_required_fields() -> None:
    """Required fields must be provided."""
    with pytest.raises(ValidationError):
        SampleOutputs(resource_group_name="my-rg")  # type: ignore[call-arg]


def test_model_validation_rejects_wrong_types() -> None:
    """Fields with wrong types are rejected."""
    with pytest.raises(ValidationError):
        SampleOutputs(resource_group_name=123, vnet_id="ok")  # type: ignore[arg-type]
