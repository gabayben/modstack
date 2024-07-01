from abc import ABC, abstractmethod
from typing import Optional, TypedDict

from modstack.artifacts import Artifact

class ArtifactQuery(TypedDict, total=False):
    artifact_ids: Optional[list[str]]
    ref_artifact_ids: Optional[list[str]]

class ArtifactRepository(ABC):
    @abstractmethod
    def get(self, artifact_id: str, **kwargs) -> Optional[Artifact]:
        pass

    @abstractmethod
    async def aget(self, artifact_id: str, **kwargs) -> Optional[Artifact]:
        pass

    @abstractmethod
    def get_many(self, query: ArtifactQuery = {}, **kwargs) -> list[Artifact]:
        pass

    @abstractmethod
    async def aget_many(self, query: ArtifactQuery = {}, **kwargs) -> list[Artifact]:
        pass

    @abstractmethod
    def insert(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    @abstractmethod
    async def ainsert(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    @abstractmethod
    def delete(self, artifact_id: str, **kwargs) -> None:
        pass

    @abstractmethod
    async def adelete(self, artifact_id: str, **kwargs) -> None:
        pass

    @abstractmethod
    def delete_many(self, query: ArtifactQuery = {}, **kwargs) -> None:
        pass

    @abstractmethod
    async def adelete_many(self, query: ArtifactQuery = {}, **kwargs) -> None:
        pass