from abc import ABC, abstractmethod
from typing import Optional

from modstack.artifacts import Artifact
from modstack.data.stores import VectorStoreQuery, VectorStoreQueryResult
from modstack.typing import MetadataFilters

class VectorStore(ABC):
    @abstractmethod
    def retrieve(self, query: VectorStoreQuery, **kwargs) -> VectorStoreQueryResult:
        pass

    @abstractmethod
    async def aretrieve(self, query: VectorStoreQuery, **kwargs) -> VectorStoreQueryResult:
        pass

    @abstractmethod
    def insert(self, artifacts: list[Artifact], **kwargs) -> list[str]:
        pass

    @abstractmethod
    async def ainsert(self, artifacts: list[Artifact], **kwargs) -> list[str]:
        pass

    @abstractmethod
    def delete(
        self,
        artifact_ids: Optional[list[str]] = None,
        filters: Optional[MetadataFilters] = None,
        **kwargs
    ) -> None:
        pass

    @abstractmethod
    async def adelete(
        self,
        artifact_ids: Optional[list[str]] = None,
        filters: Optional[MetadataFilters] = None,
        **kwargs
    ) -> None:
        pass

    @abstractmethod
    def delete_ref(self, ref_artifact_id: str, **kwargs) -> None:
        pass

    @abstractmethod
    async def adelete_ref(self, ref_artifact_id: str, **kwargs) -> None:
        pass

    @abstractmethod
    def clear(self, **kwargs) -> None:
        pass

    @abstractmethod
    async def aclear(self, **kwargs) -> None:
        pass