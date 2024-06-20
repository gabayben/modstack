from typing import Any, Optional

import chromadb
from chromadb.api.models.Collection import Collection

from modstack.artifacts import Artifact
from modstack.stores.vector import VectorStore, VectorStoreQuery, VectorStoreQueryResult
from modstack.typing import MetadataFilters
from modstack.utils.threading import run_async

class ChromaVectorStore(VectorStore):
    _collection: Collection
    collection_name: Optional[str]
    collection_kwargs: dict[str, Any]
    host: Optional[str]
    port: Optional[int]
    headers: Optional[dict[str, str]]
    ssl: bool
    stores_text: bool = True
    is_flat_metadata: bool = True

    def __init__(
        self,
        collection: Optional[Collection] = None,
        collection_name: Optional[str] = None,
        collection_kwargs: Optional[dict[str, Any]] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        headers: Optional[dict[str, str]] = None,
        ssl: bool = False
    ):
        self.collection_name = collection_name
        self.collection_kwargs = collection_kwargs or {}
        self.host = host
        self.port = port
        self.headers = headers
        self.ssl = ssl
        if collection is None:
            client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                headers=self.headers,
                ssl=self.ssl
            )
            self._collection = client.get_or_create_collection(
                name=collection_name,
                **collection_kwargs
            )
        else:
            self._collection = collection

    def retrieve(self, query: VectorStoreQuery, **kwargs) -> VectorStoreQueryResult:
        pass

    async def aretrieve(self, query: VectorStoreQuery, **kwargs) -> VectorStoreQueryResult:
        return await run_async(self.retrieve, query, **kwargs)

    def insert(self, artifacts: list[Artifact], **kwargs) -> list[str]:
        pass

    async def ainsert(self, artifacts: list[Artifact], **kwargs) -> list[str]:
        return await run_async(self.insert, artifacts, **kwargs)

    def delete(
        self,
        artifact_ids: Optional[list[str]] = None,
        filters: Optional[MetadataFilters] = None,
        **kwargs
    ) -> None:
        pass

    async def adelete(
        self,
        artifact_ids: Optional[list[str]] = None,
        filters: Optional[MetadataFilters] = None,
        **kwargs
    ) -> None:
        await run_async(self.delete, artifact_ids, filters, **kwargs)

    def delete_ref(self, ref_artifact_id: str, **kwargs) -> None:
        pass

    async def adelete_ref(self, ref_artifact_id: str, **kwargs) -> None:
        await run_async(self.delete_ref, ref_artifact_id, **kwargs)

    def clear(self, **kwargs) -> None:
        pass

    async def aclear(self, **kwargs) -> None:
        await run_async(self.clear, **kwargs)

    def _get(
        self,
        limit: Optional[int],
        where: dict,
        **kwargs
    ) -> VectorStoreQueryResult:
        pass