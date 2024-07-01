from typing import Optional

from modstack.data.querying.indices.structs import IndexStruct, index_struct_registry
from modstack.stores.index import IndexStore
from modstack.stores.keyvalue import KVStore

DEFAULT_NAMESPACE = 'index_store'
DEFAULT_COLLECTION = 'data'

class KVIndexStore(IndexStore):
    def __init__(
        self,
        kvstore: KVStore,
        namespace: Optional[str] = None,
        collection: Optional[str] = None
    ):
        self._kvstore = kvstore
        namespace = namespace or DEFAULT_NAMESPACE
        collection = collection or DEFAULT_COLLECTION
        self._collection = f'{namespace}/{collection}'

    def get_struct(self, struct_id: Optional[str] = None, **kwargs) -> Optional[IndexStruct]:
        if struct_id is None:
            structs = self.structs(**kwargs)
            assert len(structs) == 1
            return structs[0]
        data = self._kvstore.get(struct_id, collection=self._collection, **kwargs)
        return index_struct_registry.deserialize(data) if data is not None else None

    async def aget_struct(self, struct_id: Optional[str] = None, **kwargs) -> Optional[IndexStruct]:
        if struct_id is None:
            structs = await self.astructs(**kwargs)
            assert len(structs) == 1
            return structs[0]
        data = await self._kvstore.aget(struct_id, collection=self._collection, **kwargs)
        return index_struct_registry.deserialize(data) if data is not None else None

    def structs(self, **kwargs) -> list[IndexStruct]:
        all_data = self._kvstore.get_all(collection=self._collection, **kwargs)
        return [index_struct_registry.deserialize(data) for data in all_data.values()]

    async def astructs(self, **kwargs) -> list[IndexStruct]:
        all_data = await self._kvstore.aget_all(collection=self._collection, **kwargs)
        return [index_struct_registry.deserialize(data) for data in all_data.values()]

    def upsert_struct(self, struct: IndexStruct, **kwargs) -> None:
        self._kvstore.put(
            struct.index_id,
            struct.model_dump(),
            collection=self._collection,
            **kwargs
        )

    async def aupsert_struct(self, struct: IndexStruct, **kwargs) -> None:
        await self._kvstore.aput(
            struct.index_id,
            struct.model_dump(),
            collection=self._collection,
            **kwargs
        )

    def delete_struct(self, struct_id: str, **kwargs) -> None:
        self._kvstore.delete(struct_id, collection=self._collection, **kwargs)

    async def adelete_struct(self, struct_id: str, **kwargs) -> None:
        await self._kvstore.adelete(struct_id, collection=self._collection, **kwargs)