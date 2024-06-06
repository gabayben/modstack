from abc import ABC, abstractmethod
from typing import Optional

from modstack.index_structs import IndexStruct

class IndexStore(ABC):
    @abstractmethod
    def get_struct(self, struct_id: Optional[str] = None, **kwargs) -> Optional[IndexStruct]:
        pass

    @abstractmethod
    def structs(self, **kwargs) -> list[IndexStruct]:
        pass

    @abstractmethod
    def add_struct(self, struct: IndexStruct, **kwargs) -> None:
        pass

    @abstractmethod
    def delete_struct(self, struct_id: str, **kwargs) -> None:
        pass