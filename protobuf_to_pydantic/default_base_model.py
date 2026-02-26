"""Default base model for protobuf_to_pydantic generated models."""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import (
    AliasGenerator,
    BaseModel,
    ConfigDict,
    FieldSerializationInfo,
    SerializerFunctionWrapHandler,
    field_serializer,
    model_serializer,
    model_validator,
)
from pydantic.alias_generators import to_camel


class ProtobufCompatibleBaseModel(BaseModel):
    """Base model for protobuf-generated Pydantic models with protobuf-compatible settings"""

    model_config = ConfigDict(
        # Serialize inf/-inf/nan as "Infinity"/"-Infinity"/"NaN" strings
        # to match protobuf's JSON serialization format
        ser_json_inf_nan="strings",
        # Add alias generation settings
        alias_generator=AliasGenerator(
            validation_alias=to_camel,
            serialization_alias=to_camel,
        ),
        populate_by_name=True,
    )

    @model_serializer(mode="wrap")
    def serialize_model(self, nxt):
        output = nxt(self)
        if not hasattr(self, "_oneof_fields"):
            return output
        union_fields: dict[str, dict[str, dict[str, str]]] = self._oneof_fields  # type: ignore
        for field_name in union_fields.keys():
            if field_name not in output:
                continue
            field_value = output[field_name]
            output.pop(field_name)

            if field_value:
                output.update(field_value)
        return output

    @field_serializer("*", when_used="json", mode="wrap")
    def _serialize_enums(
        self,
        value: Any,
        nxt: SerializerFunctionWrapHandler,
        info: FieldSerializationInfo,
    ) -> Any:
        if isinstance(value, Enum):
            return value.name
        return nxt(value)

    @model_validator(mode="before")
    @classmethod
    def _deserialize_oneofs(cls, data):
        """Handle oneof field deserialization from flat JSON."""
        if not isinstance(data, dict):
            return data

        if not hasattr(cls, "_oneof_fields"):
            return data

        # Get the actual value from ModelPrivateAttr if needed
        union_fields = cls._oneof_fields  # type: ignore
        if hasattr(union_fields, "default"):
            union_fields = union_fields.default

        # Process each discriminated union field
        for field_name, field_info in union_fields.items():
            if field_name not in data:
                field_aliases = field_info.get("aliases", {})

                # Check if any oneof field is present in flat format
                present_fields = []
                field_mapping = {}
                for key in data:
                    if data[key] is None:
                        continue
                    if key in field_aliases:
                        actual_field = field_aliases[key]
                        if actual_field in field_mapping:
                            # Same field specified via different alias
                            raise ValueError(
                                f"Field '{actual_field}' specified multiple times in oneof '{field_name}' "
                                f"using different aliases: '{field_mapping[actual_field]}' and '{key}'. "
                                f"Only one field allowed."
                            )

                        present_fields.append(actual_field)
                        field_mapping[actual_field] = key

                if len(present_fields) > 1:
                    raise ValueError(
                        f"Multiple fields from oneof '{field_name}' specified: {', '.join(present_fields)}. "
                        f"Only one field allowed."
                    )
                if present_fields:
                    actual_field = present_fields[0]
                    data_key = field_mapping[actual_field]
                    data[field_name] = {
                        actual_field: data.pop(data_key),
                        f"{field_name}_case": actual_field,
                    }

        return data

    # ------------------------------------------------------------
    # Don't serialize unset fields, or fields with default values
    # ------------------------------------------------------------
    def model_dump(
        self,
        *,
        mode: str = "python",
        include: Optional[Any] = None,
        exclude: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
        by_alias: bool = False,
        exclude_unset: bool = False, 
        exclude_defaults: bool = False,
        exclude_none: bool = False, 
        round_trip: bool = False,
        warnings: bool = True,
        serialize_as_any: bool = False,
    ) -> Dict[str, Any]:
        """Override model_dump to exclude defaults and unset fields by default."""
        return super().model_dump(
            mode=mode,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
        )

    def model_dump_json(
        self,
        *,
        indent: Optional[int] = None,
        include: Optional[Any] = None,
        exclude: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
        by_alias: bool = False,
        exclude_unset: bool = False, 
        exclude_defaults: bool = False,
        exclude_none: bool = False, 
        round_trip: bool = False,
        warnings: bool = True,
        serialize_as_any: bool = False,
    ) -> str:
        """Override model_dump_json to exclude defaults and unset fields by default."""
        return super().model_dump_json(
            indent=indent,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
        )


# Default base model to use if none is specified
default_base_model = ProtobufCompatibleBaseModel
