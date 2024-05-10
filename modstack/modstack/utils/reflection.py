import inspect
from typing import Type

def get_members[T](obj: object, type_: Type[T]) -> list[tuple[str, T]]:
    return inspect.getmembers(obj, lambda x: isinstance(x, type_))