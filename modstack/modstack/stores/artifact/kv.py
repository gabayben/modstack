from typing import Optional, Sequence

from modstack.artifacts import Artifact
from modstack.stores.artifact import ArtifactStore, RefArtifactInfo
from modstack.stores.keyvalue import KVStore
from modstack.utils.constants import DEFAULT_STORAGE_BATCH_SIZE

DEFAULT_NAMESPACE = 'docstore'
DEFAULT_DATA_COLLECTION = 'data'
DEFAULT_REF_ARTIFACT_COLLECTION = 'ref_artifact_info'
DEFAULT_METADATA_COLLECTION = 'metadata'

class KVArtifactStore(ArtifactStore):
    def __init__(
        self,
        kvstore: KVStore,
        namespace: Optional[str] = None,
        data_collection: Optional[str] = None,
        ref_artifact_collection: Optional[str] = None,
        metadata_collection: Optional[str] = None,
        batch_size: int = DEFAULT_STORAGE_BATCH_SIZE
    ):
        self.kvstore = kvstore
        namespace = namespace or DEFAULT_NAMESPACE
        data_collection = data_collection or DEFAULT_DATA_COLLECTION
        ref_artifact_collection = ref_artifact_collection or DEFAULT_REF_ARTIFACT_COLLECTION
        metadata_collection = metadata_collection or DEFAULT_METADATA_COLLECTION
        self._data_collection = f'{namespace}/{data_collection}'
        self._ref_artifact_collection = f'{namespace}/{ref_artifact_collection}'
        self._metadata_collection = f'{namespace}/{metadata_collection}'
        self._batch_size = batch_size

    #### Artifacts

    def get(
        self,
        artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> Optional[Artifact]:
        pass

    async def aget(
        self,
        artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> Optional[Artifact]:
        pass

    def get_many(
        self,
        artifact_ids: Sequence[str],
        raise_error: bool = True,
        **kwargs
    ) -> list[Artifact]:
        pass

    async def aget_many(
        self,
        artifact_ids: Sequence[str],
        raise_error: bool = True,
        **kwargs
    ) -> list[Artifact]:
        pass

    def get_index_dict(self, ids_by_index: dict[int, str], **kwargs) -> dict[int, Artifact]:
        pass

    async def aget_index_dict(self, ids_by_index: dict[int, str], **kwargs) -> dict[int, Artifact]:
        pass

    def get_all(self, **kwargs) -> dict[str, Artifact]:
        pass

    async def aget_all(self, **kwargs) -> dict[str, Artifact]:
        pass

    def exists(self, artifact_id: str) -> bool:
        pass

    async def aexists(self, artifact_id: str) -> bool:
        pass

    def insert(
        self,
        artifacts: Sequence[Artifact],
        batch_size: int = DEFAULT_STORAGE_BATCH_SIZE,
        allow_update: bool = True,
        store_content: bool = True
    ) -> None:
        pass

    async def ainsert(
        self,
        artifacts: Sequence[Artifact],
        batch_size: int = DEFAULT_STORAGE_BATCH_SIZE,
        allow_update: bool = True,
        store_content: bool = True
    ) -> None:
        pass

    def delete(
        self,
        artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> None:
        pass

    async def adelete(
        self,
        artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> None:
        pass

    #### Artifact Hashes

    def get_hash(self, artifact_id: str, **kwargs) -> Optional[str]:
        pass

    async def aget_hash(self, artifact_id: str, **kwargs) -> Optional[str]:
        pass

    def get_all_hashes(self, **kwargs) -> dict[str, str]:
        pass

    async def aget_all_hashes(self, **kwargs) -> dict[str, str]:
        pass

    def set_hash(
        self,
        artifact_id: str,
        artifact_hash: str,
        **kwargs
    ) -> None:
        pass

    async def aset_hash(
        self,
        artifact_id: str,
        artifact_hash: str,
        **kwargs
    ) -> None:
        pass

    #### Ref Artifacts

    def get_ref(self, ref_artifact_id: str, **kwargs) -> Optional[RefArtifactInfo]:
        pass

    async def aget_ref(self, ref_artifact_id: str, **kwargs) -> Optional[RefArtifactInfo]:
        pass

    def get_all_refs(self, **kwargs) -> Optional[dict[str, RefArtifactInfo]]:
        pass

    async def aget_all_refs(self, **kwargs) -> Optional[dict[str, RefArtifactInfo]]:
        pass

    def delete_ref(
        self,
        ref_artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> None:
        pass

    async def adelete_ref(
        self, ref_artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> None:
        pass