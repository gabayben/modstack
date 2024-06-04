from abc import ABC, abstractmethod
from typing import Literal, Optional, Sequence, overload

from modstack.artifacts import Artifact
from modstack.stores.artifact import RefArtifactInfo
from modstack.utils.constants import DEFAULT_STORAGE_BATCH_SIZE

class ArtifactStore(ABC):

    #### Artifacts

    @overload
    def get(
        self,
        artifact_id: str,
        raise_error: Literal[True] = True,
        **kwargs
    ) -> Artifact:
        ...

    @overload
    def get(
        self,
        artifact_id: str,
        raise_error: Literal[False] = False,
        **kwargs
    ) -> Optional[Artifact]:
        ...

    @abstractmethod
    def get(
        self,
        artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> Optional[Artifact]:
        pass

    @overload
    async def aget(
        self,
        artifact_id: str,
        raise_error: Literal[True] = True,
        **kwargs
    ) -> Artifact:
        ...

    @overload
    async def aget(
        self,
        artifact_id: str,
        raise_error: Literal[False] = False,
        **kwargs
    ) -> Optional[Artifact]:
        ...

    @abstractmethod
    async def aget(
        self,
        artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> Optional[Artifact]:
        pass

    @abstractmethod
    def get_many(
        self,
        artifact_ids: Sequence[str],
        raise_error: bool = True,
        **kwargs
    ) -> list[Artifact]:
        pass

    @abstractmethod
    async def aget_many(
        self,
        artifact_ids: Sequence[str],
        raise_error: bool = True,
        **kwargs
    ) -> list[Artifact]:
        pass

    @abstractmethod
    def get_index_dict(self, ids_by_index: dict[int, str], **kwargs) -> dict[int, Artifact]:
        pass

    @abstractmethod
    async def aget_index_dict(self, ids_by_index: dict[int, str], **kwargs) -> dict[int, Artifact]:
        pass

    @abstractmethod
    def get_all(self, **kwargs) -> dict[str, Artifact]:
        pass

    @abstractmethod
    async def aget_all(self, **kwargs) -> dict[str, Artifact]:
        pass

    def exists(self, artifact_id: str) -> bool:
        return self.get(artifact_id, raise_error=False) is not None

    async def aexists(self, artifact_id: str) -> bool:
        return (await self.aget(artifact_id, raise_error=False)) is not None

    @abstractmethod
    def insert(
        self,
        artifacts: Sequence[Artifact],
        batch_size: int = DEFAULT_STORAGE_BATCH_SIZE,
        allow_update: bool = True,
        store_content: bool = True
    ) -> None:
        pass

    @abstractmethod
    async def ainsert(
        self,
        artifacts: Sequence[Artifact],
        batch_size: int = DEFAULT_STORAGE_BATCH_SIZE,
        allow_update: bool = True,
        store_content: bool = True
    ) -> None:
        pass

    @abstractmethod
    def delete(
        self,
        artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> None:
        pass

    @abstractmethod
    async def adelete(
        self,
        artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> None:
        pass

    #### Artifact Hashes

    @abstractmethod
    def get_hash(self, artifact_id: str, **kwargs) -> Optional[str]:
        pass

    @abstractmethod
    async def aget_hash(self, artifact_id: str, **kwargs) -> Optional[str]:
        pass

    @abstractmethod
    def get_all_hashes(self, **kwargs) -> dict[str, str]:
        pass

    @abstractmethod
    async def aget_all_hashes(self, **kwargs) -> dict[str, str]:
        pass

    @abstractmethod
    def set_hash(
        self,
        artifact_id: str,
        artifact_hash: str,
        **kwargs
    ) -> None:
        pass

    @abstractmethod
    async def aset_hash(
        self,
        artifact_id: str,
        artifact_hash: str,
        **kwargs
    ) -> None:
        pass

    def set_hashes(self, artifact_hashes: dict[str, str], **kwargs) -> None:
        for artifact_id, artifact_hash in artifact_hashes.items():
            self.set_hash(artifact_id, artifact_hash, **kwargs)

    async def aset_hashes(self, artifact_hashes: dict[str, str], **kwargs) -> None:
        for artifact_id, artifact_hash in artifact_hashes.items():
            await self.aset_hash(artifact_id, artifact_hash, **kwargs)

    #### Ref Artifacts

    @abstractmethod
    def get_ref(self, ref_artifact_id: str, **kwargs) -> Optional[RefArtifactInfo]:
        pass

    @abstractmethod
    async def aget_ref(self, ref_artifact_id: str, **kwargs) -> Optional[RefArtifactInfo]:
        pass

    def ref_exists(self, ref_artifact_id: str) -> bool:
        return self.get_ref(ref_artifact_id) is not None

    async def aref_exists(self, ref_artifact_id: str) -> bool:
        return (await self.aget_ref(ref_artifact_id)) is not None

    @abstractmethod
    def delete_ref(
        self,
        ref_artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> None:
        pass

    @abstractmethod
    async def adelete_ref(
        self,
        ref_artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> None:
        pass