from typing import Optional

from modstack.artifacts import Artifact
from modstack.stores.vector import VectorStore, VectorStoreQuery, VectorStoreQueryResult
from modstack.typing import MetadataFilters

class SimpleVectorStore(VectorStore):
    def retrieve(self, query: VectorStoreQuery, **kwargs) -> VectorStoreQueryResult:
        pass

    async def aretrieve(self, query: VectorStoreQuery, **kwargs) -> VectorStoreQueryResult:
        pass

    def insert(self, artifacts: list[Artifact], **kwargs) -> list[str]:
        pass

    async def ainsert(self, artifacts: list[Artifact], **kwargs) -> list[str]:
        pass

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
        pass

    def delete_ref(self, ref_artifact_id: str, **kwargs) -> None:
        pass

    async def adelete_ref(self, ref_artifact_id: str, **kwargs) -> None:
        pass

    def clear(self, **kwargs) -> None:
        pass

    async def aclear(self, **kwargs) -> None:
        pass