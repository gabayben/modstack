from typing import Optional

from modstack.index_structs import IndexStruct
from modstack.stores.index import IndexStore

class KVIndexStore(IndexStore):
    def get_struct(self, struct_id: Optional[str] = None, **kwargs) -> Optional[IndexStruct]:
        pass

    def structs(self, **kwargs) -> list[IndexStruct]:
        pass

    def add_struct(self, struct: IndexStruct, **kwargs) -> None:
        pass

    def delete_struct(self, struct_id: str, **kwargs) -> None:
        pass