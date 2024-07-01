import json
import logging
import os.path
from typing import Optional, Self

import fsspec

from modstack.data.stores import KVStore
from modstack.data.stores.keyvalue.base import DEFAULT_COLLECTION

logger = logging.getLogger(__name__)
_DATA_TYPE = dict[str, dict[str, dict]]

class SimpleKVStore(KVStore):
    def __init__(self, data: Optional[_DATA_TYPE] = None):
        self._data: _DATA_TYPE = data or {}

    @classmethod
    def from_persist_path(
        cls,
        path: str,
        fs: Optional[fsspec.AbstractFileSystem] = None,
        **kwargs
    ) -> Self:
        fs = fs or fsspec.filesystem('file')
        logger.debug(f'Loading {__name__} from {path}.')
        with fs.open(path, 'rb') as f:
            data = json.load(f)
        return cls(data)

    def persist(
        self,
        path: str,
        fs: Optional[fsspec.AbstractFileSystem] = None,
        **kwargs
    ) -> None:
        fs = fs or fsspec.filesystem('file', **kwargs)
        dirpath = os.path.dirname(path)
        if fs.exists(dirpath):
            fs.makedirs(dirpath)
        with fs.open(path, 'w') as f:
            f.write(json.dumps(self._data))

    def get(
        self,
        key: str,
        collection: str = DEFAULT_COLLECTION,
        **kwargs
    ) -> Optional[dict]:
        collection_data = self._data.get(collection, None)
        if not collection_data or key not in collection_data:
            return None
        return collection_data[key].copy()

    async def aget(
        self,
        key: str,
        collection: str = DEFAULT_COLLECTION,
        **kwargs
    ) -> Optional[dict]:
        return self.get(key, collection=collection, **kwargs)

    def get_all(self, collection: str = DEFAULT_COLLECTION, **kwargs) -> dict[str, dict]:
        return self._data.get(collection, {}).copy()

    async def aget_all(self, collection: str = DEFAULT_COLLECTION, **kwargs) -> dict[str, dict]:
        return self.get_all(collection=collection, **kwargs)

    def put(
        self,
        key: str,
        value: dict,
        collection: str = DEFAULT_COLLECTION,
        **kwargs
    ) -> None:
        if collection not in self._data:
            self._data[collection] = {}
        self._data[collection][key] = value.copy()

    async def aput(
        self,
        key: str,
        value: dict,
        collection: str = DEFAULT_COLLECTION,
        **kwargs
    ) -> None:
        self.put(key, value, collection=collection, **kwargs)

    def delete(
        self,
        key: str,
        collection: str = DEFAULT_COLLECTION,
        **kwargs
    ) -> bool:
        try:
            self._data.pop(key)
            return True
        except KeyError:
            return False

    async def adelete(
        self,
        key: str,
        collection: str = DEFAULT_COLLECTION,
        **kwargs
    ) -> bool:
        return self.delete(key, collection=collection, **kwargs)