from abc import ABC, abstractmethod
from typing import Optional

from modstack.index_structs import IndexStruct

class IndexStore(ABC):
    @abstractmethod
    def get_struct(self, struct_id: Optional[str] = None, **kwargs) -> Optional[IndexStruct]:
        pass

    @abstractmethod
    async def aget_struct(self, struct_id: Optional[str] = None, **kwargs) -> Optional[IndexStruct]:
        pass

    @abstractmethod
    def structs(self, **kwargs) -> list[IndexStruct]:
        pass

    @abstractmethod
    async def astructs(self, **kwargs) -> list[IndexStruct]:
        pass

    @abstractmethod
    def insert_struct(self, struct: IndexStruct, **kwargs) -> None:
        pass

    @abstractmethod
    async def ainsert_struct(self, struct: IndexStruct, **kwargs) -> None:
        pass

    @abstractmethod
    def delete_struct(self, struct_id: str, **kwargs) -> None:
        pass

    @abstractmethod
    async def adelete_struct(self, struct_id: str, **kwargs) -> None:
        pass