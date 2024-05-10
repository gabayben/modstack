import inspect
from typing import Callable, Type

from overrides.typing_utils import get_type_hints, issubtype

def get_return_type[R](func: Callable[..., R]) -> Type[R]:
    return get_type_hints(func)['return']

def is_return_type[R, T](func: Callable[..., R], type_: Type[T]) -> bool:
    return issubtype(get_return_type(func), type_)

def get_members[T](obj: object, type_: Type[T]) -> list[tuple[str, T]]:
    return inspect.getmembers(obj, lambda x: isinstance(x, type_))

def is_typed_dict(type_: Type) -> bool:
    return type_.__class__.__name__ == '_TypedDictMeta'

def is_named_tuple(type_: Type) -> bool:
    return issubclass(type_, tuple) and hasattr(type_, '_asdict') and hasattr(type_, '_fields')

def is_not_required(type_: Type) -> bool:
    return type_.__name__ == 'NotRequired'