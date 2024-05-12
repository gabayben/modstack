from functools import lru_cache
from typing import Any, Type

from pydantic import BaseModel, ConfigDict, create_model as create_model_base
from pydantic.main import Model

from modstack.utils.reflection import is_named_tuple, is_not_required, is_typed_dict

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
        return _create_model_cached(__model_name, **field_descriptions)
    except TypeError:
        # something in field definitions is not hashable
        return create_model_base(
            __model_name,
            __config__= __config__ or _SchemaConfig(extra='allow', arbitrary_types_allowed=True),
            __doc__=__doc__,
            __module__=__module__,
            __validators__=__validators__,
            __cls_kwargs__=__cls_kwargs__,
            __slots__=__slots__,
            **field_descriptions
        )

def create_schema[T](name: str, type_: Type[T]) -> Type[BaseModel]:
    if issubclass(type_.__class__, BaseModel):
        return type_

    field_descriptions: dict[str, (Type, Any)]

    if is_typed_dict(type_):
        field_descriptions = {
            k: (v.__args__[0], None) if is_not_required(v) else (v, ...)
            for k, v in type_.__annotations__.items()
        }
    elif is_named_tuple(type_):
        field_descriptions = {
            k: (v, type_._field_defaults[k]) if k in type_._field_defaults else (v, ...)
            for k, v in type_.__annotations__.items()
        }
    else:
        field_descriptions = {'value': (type_, ...)}

    return create_model(name, **field_descriptions)

def to_dict(data: Any) -> dict[str, Any]:
    if isinstance(data, dict):
        return data
    elif isinstance(data, BaseModel):
        return dict(data)
    elif is_named_tuple(type(data)):
        return data._asdict()
    return {'value': data}