import asyncio
from typing import Optional

from modstack.artifacts import Artifact, artifact_registry
from modstack.stores.keyvalue import KVStore

class InjestionCache:
    def __init__(
        self,
        kvstore: KVStore,
        collection: Optional[str] = None,
        artifacts_key: Optional[str] = None
    ):
        self._kvstore = kvstore
        self._collection = collection or 'modstack_cache'
        self._artifacts_key = artifacts_key or 'artifacts'

    def get(self, key: str, collection: Optional[str] = None) -> Optional[list[Artifact]]:
        collection = collection or self._collection
        data = self._kvstore.get(key, collection=collection)
        if data is None:
            return None
        return [artifact_registry.deserialize(entry) for entry in data]

    async def aget(self, key: str, collection: Optional[str] = None) -> Optional[list[Artifact]]:
        collection = collection or self._collection
        data = await self._kvstore.aget(key, collection=collection)
        if data is None:
            return None
        return [artifact_registry.deserialize(entry) for entry in data]

    def put(
        self,
        key: str,
        artifacts: list[Artifact],
        collection: Optional[str] = None
    ) -> None:
        collection = collection or self._collection
        self._kvstore.put(
            key,
            {self._artifacts_key: [artifact.model_dump() for artifact in artifacts]},
            collection=collection
        )

    async def aput(
        self,
        key: str,
        artifacts: list[Artifact],
        collection: Optional[str] = None
    ) -> None:
        collection = collection or self._collection
        await self._kvstore.aput(
            key,
            {self._artifacts_key: [artifact.model_dump() for artifact in artifacts]},
            collection=collection
        )

    def clear(self, collection: Optional[str] = None) -> None:
        collection = collection or self._collection
        all_data = self._kvstore.get_all(collection=collection)
        for key in all_data:
            self._kvstore.delete(key, collection=collection)

    async def aclear(self, collection: Optional[str] = None) -> None:
        collection = collection or self._collection
        all_data = await self._kvstore.aget_all(collection=collection)
        await asyncio.gather(
            self._kvstore.adelete(key, collection=collection)
            for key in all_data
        )