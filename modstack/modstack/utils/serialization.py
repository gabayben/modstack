from functools import lru_cache
import inspect
from inspect import Parameter
from typing import Any, Callable, NamedTuple, Type

from pydantic import BaseModel, ConfigDict, create_model as create_model_base
from pydantic.main import Model

from modstack.utils.constants import SCHEMA_TYPE
from modstack.typing import Schema, SchemaType
from modstack.utils.reflection import is_named_tuple

class _SchemaConfig(ConfigDict):
    pass

@lru_cache(maxsize=256)
def _create_model_cached(
    __model_name: str,
    *,
    __config__: ConfigDict | None = None,
    __doc__: str | None = None,
    __base__: Type[Model] | tuple[Type[Model], ...] | None = None,
    __module__: str | None = None,
    __validators__: dict[str, classmethod] | None = None,
    __cls_kwargs__: dict[str, Any] | None = None,
    __slots__: tuple[str, ...] | None = None,
    **field_definitions
) -> Type[BaseModel]:
    return create_model_base(
        __model_name,
        __config__=_SchemaConfig(extra='allow', arbitrary_types_allowed=True),
        **field_definitions
    )

def create_model(
    __model_name: str,
    *,
    __config__: ConfigDict | None = None,
    __doc__: str | None = None,
    __base__: Type[Model] | tuple[Type[Model], ...] | None = None,
    __module__: str | None = None,
    __validators__: dict[str, classmethod] | None = None,
    __cls_kwargs__: dict[str, Any] | None = None,
    __slots__: tuple[str, ...] | None = None,
    **field_descriptions
) -> Type[BaseModel]:
    try:
        return _create_model_cached(
            __model_name,
            __config__=_SchemaConfig(extra='allow', arbitrary_types_allowed=True, **(__config__ or {})),
            __doc__=__doc__,
            __module__=__module__,
            __validators__=__validators__,
            __cls_kwargs__=__cls_kwargs__,
            __slots__=__slots__,
            **field_descriptions
        )
    except TypeError:
        # something in field definitions is not hashable
        return create_model_base(
            __model_name,
            __config__=_SchemaConfig(extra='allow', arbitrary_types_allowed=True, **(__config__ or {})),
            __doc__=__doc__,
            __module__=__module__,
            __validators__=__validators__,
            __cls_kwargs__=__cls_kwargs__,
            __slots__=__slots__,
            **field_descriptions
        )

def model_from_callable(name: str, func: Callable) -> Type[BaseModel]:
    signature = inspect.signature(func)
    return create_model(
        name,
        **from_parameters(dict(signature.parameters))
    )

def create_schema[T](name: str, type_: Type[T]) -> Type[BaseModel]:
    if issubclass(type_.__class__, Schema):
        return type_
    return create_model(
        name,
        __config__={SCHEMA_TYPE: SchemaType.VALUE},
        value=(type_, ...)
    )

def from_parameters(parameters: dict[str, Parameter]) -> dict[str, tuple[Any, Any | None]]:
    return {
        name: (
            (parameter.annotation, parameter.default)
            if parameter.default != inspect.Parameter.empty
            else (parameter.annotation, ...)
        )
        for name, parameter in parameters.items()
        if parameter.annotation != inspect.Parameter.empty
    }

def from_dict(data: dict[str, Any], input_schema: Type[BaseModel]) -> Any:
    schema_type = input_schema.model_config.get(SCHEMA_TYPE, None)
    if isinstance(input_schema, Schema):
        return input_schema.model_construct(**data)
    field = (
        input_schema.model_fields.popitem()[1]
        if len(input_schema.model_fields) > 0
        else None
    )
    if field is None:
        return None
    if issubclass(field.annotation, dict):
        return data
    return data.popitem()[1] if len(data) > 0 else None

def to_dict(data: Any) -> dict[str, Any]:
    if isinstance(data, Schema):
        return data.model_dump()
    return {'value': data}