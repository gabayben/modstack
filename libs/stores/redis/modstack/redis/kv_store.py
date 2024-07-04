from typing import Optional

import fsspec

from modstack.stores import KVStore
from modstack.stores.keyvalue.base import DEFAULT_COLLECTION

class RedisKVStore(KVStore):
    def persist(
        self,
        path: str,
        fs: Optional[fsspec.AbstractFileSystem] = None,
        **kwargs
    ) -> None:
        pass

    def get(self, key: str, collection: str = DEFAULT_COLLECTION, **kwargs) -> Optional[dict]:
        pass

    async def aget(self, key: str, collection: str = DEFAULT_COLLECTION, **kwargs) -> Optional[dict]:
        pass

    def get_all(self, collection: str = DEFAULT_COLLECTION, **kwargs) -> dict[str, dict]:
        pass

    async def aget_all(self, collection: str = DEFAULT_COLLECTION, **kwargs) -> dict[str, dict]:
        pass

    def put(self, key: str, value: dict, collection: str = DEFAULT_COLLECTION, **kwargs) -> None:
        pass

    async def aput(self, key: str, value: dict, collection: str = DEFAULT_COLLECTION, **kwargs) -> None:
        pass

    def delete(self, key: str, collection: str = DEFAULT_COLLECTION, **kwargs) -> bool:
        pass

    async def adelete(self, key: str, collection: str = DEFAULT_COLLECTION, **kwargs) -> bool:
        pass