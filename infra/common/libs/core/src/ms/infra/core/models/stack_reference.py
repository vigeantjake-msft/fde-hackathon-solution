from typing import Any
from typing import Self
from typing import cast

import pulumi
from pydantic import TypeAdapter

from ms.infra.core.models.base import FrozenBaseModel

_OUTPUT_KEY_PREFIX = "_export_"


class StackOutputBaseModel(FrozenBaseModel):
    """Base class for typed stack output contracts in multi-project Pulumi repos.

    All fields should be plain types (``str``, ``int``, etc.) — no ``Output`` wrappers.
    This keeps the model strictly validated on the consumer side.

    Exported keys are automatically prefixed with ``_export_`` to avoid
    collisions with direct ``pulumi.export()`` calls. This is transparent —
    callers use plain field names and the prefix is handled internally.

    Producer (exporting project)::

        class PlatformOutputs(StackOutputBaseModel):
            resource_group_name: str
            vnet_id: str

        PlatformOutputs.export_outputs(
            resource_group_name=rg.name,
            vnet_id=vnet.id,
        )

    Consumer (importing project)::

        ref = pulumi.StackReference("organization/platform/staging")
        platform = PlatformOutputs.from_stack_reference(ref)
        # platform is Output[PlatformOutputs] — validated at deploy time
        rg_name = platform.apply(lambda p: p.resource_group_name)
    """

    @classmethod
    def from_stack_reference(cls, ref: pulumi.StackReference) -> pulumi.Output[Self]:
        """Construct a validated model instance from a StackReference.

        Resolves all declared fields from the stack reference (using the
        ``_export_``-prefixed keys), then validates them against the model schema.
        Validation runs during ``pulumi preview`` and ``pulumi up``, so
        missing or mistyped outputs are caught early.

        Args:
            ref: A Pulumi StackReference pointing to the producing stack.

        Returns:
            An Output that resolves to a validated instance of this model.

        Raises:
            pydantic.ValidationError: If resolved outputs don't match the schema
                (surfaced as a Pulumi error during preview/deploy).
        """
        # Always use get_output (not require_output) because Pulumi strips
        # None values from resource output dicts internally, making
        # require_output raise KeyError for nullable fields even when they
        # were explicitly exported as None. Pydantic's model_validate handles
        # the "required but missing" check: a missing non-nullable field
        # resolves as None and fails validation.
        outputs = {name: ref.get_output(f"{_OUTPUT_KEY_PREFIX}{name}") for name in cls.model_fields}
        return pulumi.Output.all(**outputs).apply(lambda resolved: cls.model_validate(resolved))

    @classmethod
    def export_outputs(cls, **kwargs: Any) -> None:
        """Export stack outputs, validating keys and types against the model schema.

        Accepts ``Output[T]`` values (or plain values) as keyword arguments.
        Validates that every required field is provided, no unknown fields
        are passed, and each value's type matches the field annotation.
        Keys are automatically prefixed with ``_export_`` in the exported outputs.

        We cannot use ``model_validate`` here because producer values are
        typically ``Output[T]`` (e.g. ``rg.name`` is ``Output[str]``).
        Pulumi outputs are lazy — the inner value hasn't resolved yet at
        call time, and Python erases the generic parameter at runtime, so
        an ``Output[int]`` is indistinguishable from an ``Output[str]``.
        Instead, we validate each field individually using ``TypeAdapter``:
        plain values are checked immediately, and ``Output`` values are
        checked via ``.apply()`` when they resolve at deploy time.

        Raises:
            TypeError: If provided keys don't match the model's declared fields.
            pydantic.ValidationError: If a value's type doesn't match the field
                annotation (at export time for plain values, at deploy time for
                ``Output`` values).
        """
        all_fields = set(cls.model_fields.keys())
        required_fields = {name for name, field in cls.model_fields.items() if field.is_required()}
        provided = set(kwargs.keys())
        if missing := required_fields - provided:
            raise TypeError(f"Missing outputs: {missing}")
        if extra := provided - all_fields:
            raise TypeError(f"Unexpected outputs: {extra}")
        for name, value in kwargs.items():
            annotation: type[Any] = cls.model_fields[name].annotation  # type: ignore[assignment]
            adapter: TypeAdapter[Any] = TypeAdapter(annotation)
            export_key = f"{_OUTPUT_KEY_PREFIX}{name}"

            if isinstance(value, pulumi.Output):
                output = cast(pulumi.Output[Any], value)
                pulumi.export(export_key, output.apply(lambda v, a=adapter: a.validate_python(v, strict=True)))
            else:
                adapter.validate_python(value, strict=True)
                pulumi.export(export_key, value)
