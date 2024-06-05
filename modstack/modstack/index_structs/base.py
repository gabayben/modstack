from abc import ABC

from modstack.typing import PydanticRegistry, Serializable

class IndexStruct(Serializable, ABC):
    pass

class _IndexStructRegistry(PydanticRegistry[IndexStruct]):
    pass

index_struct_registry = _IndexStructRegistry()