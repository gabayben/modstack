from typing import Optional, Sequence

from modstack.artifacts import Artifact, artifact_registry
from modstack.stores.artifact import ArtifactStore, RefArtifactInfo
from modstack.stores.keyvalue import KVStore
from modstack.utils.constants import DEFAULT_STORAGE_BATCH_SIZE

DEFAULT_NAMESPACE = 'artifact_store'
DEFAULT_DATA_COLLECTION = 'data'
DEFAULT_REF_INFO_COLLECTION = 'ref_info'
DEFAULT_METADATA_COLLECTION = 'metadata'

_Pairs = list[tuple[str, dict]]

class KVArtifactStore(ArtifactStore):
    def __init__(
        self,
        kvstore: KVStore,
        namespace: Optional[str] = None,
        data_collection: Optional[str] = None,
        ref_info_collection: Optional[str] = None,
        metadata_collection: Optional[str] = None,
        batch_size: int = DEFAULT_STORAGE_BATCH_SIZE
    ):
        self._kvstore = kvstore
        namespace = namespace or DEFAULT_NAMESPACE
        data_collection = data_collection or DEFAULT_DATA_COLLECTION
        ref_info_collection = ref_info_collection or DEFAULT_REF_INFO_COLLECTION
        metadata_collection = metadata_collection or DEFAULT_METADATA_COLLECTION
        self._data_collection = f'{namespace}/{data_collection}'
        self._ref_info_collection = f'{namespace}/{ref_info_collection}'
        self._metadata_collection = f'{namespace}/{metadata_collection}'
        self._batch_size = batch_size

    #### Artifacts

    def get(
        self,
        artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> Optional[Artifact]:
        data = self._kvstore.get(artifact_id, collection=self._data_collection, **kwargs)
        if data is None:
            if raise_error:
                raise ValueError(f"Artifact with id '{artifact_id}' not found.")
            return None
        return artifact_registry.deserialize(data)

    async def aget(
        self,
        artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> Optional[Artifact]:
        data = await self._kvstore.aget(artifact_id, collection=self._data_collection, **kwargs)
        if data is None:
            if raise_error:
                raise ValueError(f"Artifact with id '{artifact_id}' not found.")
            return None
        return artifact_registry.deserialize(data)

    def get_all(self, **kwargs) -> dict[str, Artifact]:
        data_dict = self._kvstore.get_all(collection=self._data_collection, **kwargs)
        return {name: artifact_registry.deserialize(data) for name, data in data_dict.items()}

    async def aget_all(self, **kwargs) -> dict[str, Artifact]:
        data_dict = await self._kvstore.aget_all(collection=self._data_collection, **kwargs)
        return {name: artifact_registry.deserialize(data) for name, data in data_dict.items()}

    def insert(
        self,
        artifacts: Sequence[Artifact],
        batch_size: int = DEFAULT_STORAGE_BATCH_SIZE,
        allow_update: bool = True,
        store_content: bool = True
    ) -> None:
        pass

    def _prepare_kv_pairs(
        self,
        artifacts: Sequence[Artifact],
        allow_update: bool,
        store_content: bool
    ) -> tuple[_Pairs, _Pairs, _Pairs]:
        artifact_pairs: _Pairs = []
        metadata_pairs: _Pairs = []
        ref_info_pairs: dict[str, _Pairs] = {}

    async def ainsert(
        self,
        artifacts: Sequence[Artifact],
        batch_size: int = DEFAULT_STORAGE_BATCH_SIZE,
        allow_update: bool = True,
        store_content: bool = True
    ) -> None:
        pass

    async def _aprepare_kv_pairs(
        self,
        artifacts: Sequence[Artifact],
        allow_update: bool,
        store_content: bool
    ) -> tuple[_Pairs, _Pairs, _Pairs]:
        pass

    def _merge_ref_info_pairs(self, pairs_dict: dict[str, _Pairs]) -> _Pairs:
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