from abc import ABC, abstractmethod
from typing import Optional

import fsspec

from modstack.utils.constants import DEFAULT_STORAGE_BATCH_SIZE

DEFAULT_COLLECTION = 'data'

class KVStore(ABC):
    @abstractmethod
    def persist(
        self,
        path: str,
        fs: Optional[fsspec.AbstractFileSystem] = None,
        **kwargs
    ) -> None:
        pass

    @abstractmethod
    def get(
        self,
        key: str,
        collection: str = DEFAULT_COLLECTION,
        **kwargs
    ) -> Optional[dict]:
        pass

    @abstractmethod
    async def aget(
        self,
        key: str,
        collection: str = DEFAULT_COLLECTION,
        **kwargs
    ) -> Optional[dict]:
        pass

    @abstractmethod
    def get_all(self, collection: str = DEFAULT_COLLECTION, **kwargs) -> dict[str, dict]:
        pass

    @abstractmethod
    async def aget_all(self, collection: str = DEFAULT_COLLECTION, **kwargs) -> dict[str, dict]:
        pass

    @abstractmethod
    def put(
        self,
        key: str,
        value: dict,
        collection: str = DEFAULT_COLLECTION,
        **kwargs
    ) -> None:
        pass

    @abstractmethod
    async def aput(
        self,
        key: str,
        value: dict,
        collection: str = DEFAULT_COLLECTION,
        **kwargs
    ) -> None:
        pass

    def put_all(
        self,
        entries: list[tuple[str, dict]],
        collection: str = DEFAULT_COLLECTION,
        batch_size: int = DEFAULT_STORAGE_BATCH_SIZE,
        **kwargs
    ) -> None:
        if batch_size != 1:
            raise NotImplementedError('Batching not supported by this key-value store.')
        for key, value in entries:
            self.put(key, value, collection=collection, **kwargs)

    async def aput_all(
        self,
        entries: list[tuple[str, dict]],
        collection: str = DEFAULT_COLLECTION,
        batch_size: int = DEFAULT_STORAGE_BATCH_SIZE,
        **kwargs
    ) -> None:
        if batch_size != 1:
            raise NotImplementedError('Batching not supported by this key-value store.')
        for key, value in entries:
            await self.aput(key, value, collection=collection, **kwargs)

    @abstractmethod
    def delete(
        self,
        key: str,
        collection: str = DEFAULT_COLLECTION,
        **kwargs
    ) -> bool:
        pass

    @abstractmethod
    async def adelete(
        self,
        key: str,
        collection: str = DEFAULT_COLLECTION,
        **kwargs
    ) -> bool:
        pass