import asyncio
from typing import Any, Optional, Sequence

from modstack.artifacts import Artifact, artifact_registry
from modstack.stores.artifact import ArtifactStore, RefArtifactInfo
from modstack.stores.keyvalue import KVStore
from modstack.utils.constants import DEFAULT_STORAGE_BATCH_SIZE

DEFAULT_NAMESPACE = 'artifact_store'
DEFAULT_DATA_COLLECTION = 'artifacts'
DEFAULT_REF_INFO_COLLECTION = 'refs'
DEFAULT_METADATA_COLLECTION = 'metadata'

_Pair = tuple[str, dict]
_Pairs = list[_Pair]

class KVArtifactStore(ArtifactStore):
    def __init__(
        self,
        kvstore: KVStore,
        namespace: Optional[str] = None,
        artifact_collection: Optional[str] = None,
        metadata_collection: Optional[str] = None,
        ref_collection: Optional[str] = None,
        batch_size: int = DEFAULT_STORAGE_BATCH_SIZE
    ):
        self._kvstore = kvstore
        namespace = namespace or DEFAULT_NAMESPACE
        artifact_collection = artifact_collection or DEFAULT_DATA_COLLECTION
        metadata_collection = metadata_collection or DEFAULT_METADATA_COLLECTION
        ref_collection = ref_collection or DEFAULT_REF_INFO_COLLECTION
        self._artifact_collection = f'{namespace}/{artifact_collection}'
        self._metadata_collection = f'{namespace}/{metadata_collection}'
        self._ref_collection = f'{namespace}/{ref_collection}'
        self._batch_size = batch_size

    #### Artifacts

    def get(
        self,
        artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> Optional[Artifact]:
        data = self._kvstore.get(artifact_id, collection=self._artifact_collection, **kwargs)
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
        data = await self._kvstore.aget(artifact_id, collection=self._artifact_collection, **kwargs)
        if data is None:
            if raise_error:
                raise ValueError(f"Artifact with id '{artifact_id}' not found.")
            return None
        return artifact_registry.deserialize(data)

    def get_all(self, **kwargs) -> dict[str, Artifact]:
        all_data = self._kvstore.get_all(collection=self._artifact_collection, **kwargs)
        return {name: artifact_registry.deserialize(data) for name, data in all_data.items()}

    async def aget_all(self, **kwargs) -> dict[str, Artifact]:
        all_data = await self._kvstore.aget_all(collection=self._artifact_collection, **kwargs)
        return {name: artifact_registry.deserialize(data) for name, data in all_data.items()}

    def insert(
        self,
        artifacts: Sequence[Artifact],
        batch_size: int = DEFAULT_STORAGE_BATCH_SIZE,
        allow_update: bool = True,
        store_content: bool = True
    ) -> None:
        batch_size = batch_size or self._batch_size
        artifact_pairs, metadata_pairs, ref_info_pairs = self._prepare_kv_pairs(artifacts, allow_update, store_content)
        self._kvstore.put_all(artifact_pairs, collection=self._artifact_collection, batch_size=batch_size)
        self._kvstore.put_all(metadata_pairs, collection=self._metadata_collection, batch_size=batch_size)
        self._kvstore.put_all(ref_info_pairs, collection=self._ref_collection, batch_size=batch_size)

    def _prepare_kv_pairs(
        self,
        artifacts: Sequence[Artifact],
        allow_update: bool,
        store_content: bool
    ) -> tuple[_Pairs, _Pairs, _Pairs]:
        artifact_pairs: _Pairs = []
        metadata_pairs: _Pairs = []
        ref_info_pairs: dict[str, _Pairs] = {}

        for artifact in artifacts:
            if not allow_update and self.exists(artifact.id):
                raise ValueError(
                    f"Artifact '{artifact.id}' already exists. "
                    "Set allow_update to true to overwrite."
                )

            ref_info: Optional[RefArtifactInfo] = None
            if artifact.ref is not None:
                ref_info = self.get_ref(artifact.ref.id) or RefArtifactInfo()

            artifact_pair, metadata_pair, ref_info_pair = self._get_kv_pairs(artifact, ref_info, store_content)

            if artifact_pair is not None:
                artifact_pairs.append(artifact_pair)
            if metadata_pair is not None:
                metadata_pairs.append(metadata_pair)
            if ref_info_pair is not None:
                key = ref_info_pair[0]
                if key not in ref_info_pairs:
                    ref_info_pairs[key] = []
                ref_info_pairs[key].append(ref_info_pair)

        merged_ref_info_pairs = self._merge_ref_info_pairs(ref_info_pairs)

        return artifact_pairs, metadata_pairs, merged_ref_info_pairs

    async def ainsert(
        self,
        artifacts: Sequence[Artifact],
        batch_size: int = DEFAULT_STORAGE_BATCH_SIZE,
        allow_update: bool = True,
        store_content: bool = True
    ) -> None:
        batch_size = batch_size or self._batch_size
        artifact_pairs, metadata_pairs, ref_info_pairs = await self._aprepare_kv_pairs(artifacts, allow_update, store_content)
        await asyncio.gather(
            self._kvstore.aput_all(artifact_pairs, collection=self._artifact_collection, batch_size=batch_size),
            self._kvstore.aput_all(metadata_pairs, collection=self._metadata_collection, batch_size=batch_size),
            self._kvstore.aput_all(ref_info_pairs, collection=self._ref_collection, batch_size=batch_size)
        )

    async def _aprepare_kv_pairs(
        self,
        artifacts: Sequence[Artifact],
        allow_update: bool,
        store_content: bool
    ) -> tuple[_Pairs, _Pairs, _Pairs]:
        artifact_pairs: _Pairs = []
        metadata_pairs: _Pairs = []
        ref_info_pairs: dict[str, _Pairs] = {}

        for artifact in artifacts:
            if not allow_update and await self.aexists(artifact.id):
                raise ValueError(
                    f"Artifact '{artifact.id}' already exists. "
                    "Set allow_update to true to overwrite."
                )

            ref_info: Optional[RefArtifactInfo] = None
            if artifact.ref is not None:
                ref_info = await self.aget_ref(artifact.ref.id) or RefArtifactInfo()

            artifact_pair, metadata_pair, ref_info_pair = self._get_kv_pairs(artifact, ref_info, store_content)

            if artifact_pair is not None:
                artifact_pairs.append(artifact_pair)
            if metadata_pair is not None:
                metadata_pairs.append(metadata_pair)
            if ref_info_pair is not None:
                key = ref_info_pair[0]
                if key not in ref_info_pairs:
                    ref_info_pairs[key] = []
                ref_info_pairs[key].append(ref_info_pair)

        merged_ref_info_pairs = self._merge_ref_info_pairs(ref_info_pairs)

        return artifact_pairs, metadata_pairs, merged_ref_info_pairs

    def _get_kv_pairs(
        self,
        artifact: Artifact,
        ref_info: Optional[RefArtifactInfo],
        store_content: bool
    ) -> tuple[Optional[_Pair], Optional[_Pair], Optional[_Pair]]:
        artifact_pair: Optional[_Pair] = None
        metadata_pair: Optional[_Pair] = None
        ref_info_pair: Optional[_Pair] = None

        data = artifact.model_dump()
        if store_content:
            artifact_pair = artifact.id, data

        metadata = {'hash': artifact.get_hash()}
        if ref_info is not None and artifact.ref:
            if artifact.id not in ref_info.artifact_ids:
                ref_info.artifact_ids.append(artifact.id)
            if not ref_info.metadata:
                ref_info.metadata = artifact.metadata or {}
            metadata['ref_id'] = artifact.ref.id
            metadata_pair = artifact.id, metadata
            ref_info_pair = artifact.ref.id, ref_info.to_dict()
        else:
            metadata_pair = artifact.id, metadata

        return artifact_pair, metadata_pair, ref_info_pair

    def _merge_ref_info_pairs(self, pairs_dict: dict[str, _Pairs]) -> _Pairs:
        merged_ref_info_pairs: _Pairs = []
        for key, pairs in pairs_dict.items():
            merged_artifact_ids: list[str] = []
            metadata: dict[str, Any] = {}
            for pair in pairs:
                merged_artifact_ids.extend(pair[1].get('artifact_ids'))
                metadata.update(pair[1].get('metadata', {}))
            merged_ref_info_pairs.append((
                key,
                {'artifact_ids': merged_artifact_ids, 'metadata': metadata}
            ))
        return merged_ref_info_pairs

    def delete(
        self,
        artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> None:
        self._remove_from_ref_artifact(artifact_id)
        success = self._kvstore.delete(artifact_id, collection=self._artifact_collection, **kwargs)
        self._kvstore.delete(artifact_id, collection=self._metadata_collection, **kwargs)
        if not success and raise_error:
            raise ValueError(f"Artifact with id '{artifact_id}' not found.")

    def _remove_from_ref_artifact(self, artifact_id: str) -> None:
        ref_id = self._get_ref_id(artifact_id)
        if ref_id is None:
            return
        ref_info = self.get_ref(ref_id)
        if ref_info is None:
            return
        if artifact_id in ref_info.artifact_ids:
            ref_info.artifact_ids.remove(artifact_id)
        if len(ref_info.artifact_ids) > 0:
            self._kvstore.put(ref_id, ref_info.to_dict(), collection=self._ref_collection)
        else:
            self._kvstore.delete(ref_id, collection=self._artifact_collection)
            self._kvstore.delete(ref_id, collection=self._metadata_collection)
            self._kvstore.delete(ref_id, collection=self._ref_collection)

    async def adelete(
        self,
        artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> None:
        _, success, _ = await asyncio.gather(
            self._aremove_from_ref_artifact(artifact_id),
            self._kvstore.adelete(artifact_id, collection=self._artifact_collection, **kwargs),
            self._kvstore.adelete(artifact_id, collection=self._metadata_collection, **kwargs)
        )
        if not success and raise_error:
            raise ValueError(f"Artifact with id '{artifact_id}' not found.")

    async def _aremove_from_ref_artifact(self, artifact_id: str) -> None:
        ref_id = await self._aget_ref_id(artifact_id)
        if ref_id is None:
            return
        ref_info = await self.aget_ref(ref_id)
        if ref_info is None:
            return
        if artifact_id in ref_info.artifact_ids:
            ref_info.artifact_ids.remove(artifact_id)
        if len(ref_info.artifact_ids) > 0:
            await self._kvstore.aput(ref_id, ref_info.to_dict(), collection=self._ref_collection)
        else:
            await asyncio.gather(
                self._kvstore.adelete(ref_id, collection=self._artifact_collection),
                self._kvstore.adelete(ref_id, collection=self._metadata_collection),
                self._kvstore.adelete(ref_id, collection=self._ref_collection)
            )

    #### Artifact Hashes

    def get_hash(self, artifact_id: str, **kwargs) -> Optional[str]:
        metadata = self._kvstore.get(artifact_id, collection=self._metadata_collection, **kwargs)
        if metadata is None:
            return None
        return metadata.get('hash', None)

    async def aget_hash(self, artifact_id: str, **kwargs) -> Optional[str]:
        metadata = await self._kvstore.aget(artifact_id, collection=self._metadata_collection, **kwargs)
        if metadata is None:
            return None
        return metadata.get('hash', None)

    def get_all_hashes(self, **kwargs) -> dict[str, str]:
        all_metadata = self._kvstore.get_all(collection=self._metadata_collection, **kwargs)
        return {
            metadata['hash']: artifact_id
            for artifact_id, metadata in all_metadata.items()
            if 'hash' in metadata
        }

    async def aget_all_hashes(self, **kwargs) -> dict[str, str]:
        all_metadata = await self._kvstore.aget_all(collection=self._metadata_collection, **kwargs)
        return {
            metadata['hash']: artifact_id
            for artifact_id, metadata in all_metadata.items()
            if 'hash' in metadata
        }

    def set_hash(
        self,
        artifact_id: str,
        artifact_hash: str,
        **kwargs
    ) -> None:
        self._kvstore.put(
            artifact_id,
            {'hash': artifact_hash},
            collection=self._metadata_collection,
            **kwargs
        )

    async def aset_hash(
        self,
        artifact_id: str,
        artifact_hash: str,
        **kwargs
    ) -> None:
        await self._kvstore.aput(
            artifact_id,
            {'hash': artifact_hash},
            collection=self._metadata_collection,
            **kwargs
        )

    def set_hashes(self, artifact_hashes: dict[str, str], **kwargs) -> None:
        self._kvstore.put_all(
            [
                (artifact_id, {'hash': artifact_hash})
                for artifact_id, artifact_hash in artifact_hashes.items()
            ],
            collection=self._metadata_collection,
            **kwargs
        )

    async def aset_hashes(self, artifact_hashes: dict[str, str], **kwargs) -> None:
        await self._kvstore.aput_all(
            [
                (artifact_id, {'hash': artifact_hash})
                for artifact_id, artifact_hash in artifact_hashes.items()
            ],
            collection=self._metadata_collection,
            **kwargs
        )

    #### Ref Artifacts

    def get_ref(self, ref_artifact_id: str, **kwargs) -> Optional[RefArtifactInfo]:
        data = self._kvstore.get(ref_artifact_id, collection=self._ref_collection, **kwargs)
        return self._create_ref(data) if data is not None else None

    async def aget_ref(self, ref_artifact_id: str, **kwargs) -> Optional[RefArtifactInfo]:
        data = await self._kvstore.aget(ref_artifact_id, collection=self._ref_collection, **kwargs)
        return self._create_ref(data) if data is not None else None

    def get_all_refs(self, **kwargs) -> dict[str, RefArtifactInfo]:
        all_data = self._kvstore.get_all(collection=self._ref_collection, **kwargs)
        return {ref_id: self._create_ref(data) for ref_id, data in all_data.items()}

    async def aget_all_refs(self, **kwargs) -> dict[str, RefArtifactInfo]:
        all_data = await self._kvstore.aget_all(collection=self._ref_collection, **kwargs)
        return {ref_id: self._create_ref(data) for ref_id, data in all_data.items()}

    def _create_ref(self, data: dict) -> RefArtifactInfo:
        return RefArtifactInfo(artifact_ids=data['artifact_ids'], metadata=data.get('metadata', {}))

    def _get_ref_id(self, artifact_id: str) -> Optional[str]:
        metadata = self._kvstore.get(artifact_id, collection=self._metadata_collection)
        if metadata is None:
            return None
        return metadata.get('ref_id', None)

    async def _aget_ref_id(self, artifact_id: str) -> Optional[str]:
        metadata = await self._kvstore.aget(artifact_id, collection=self._metadata_collection)
        if metadata is None:
            return None
        return metadata.get('ref_id', None)

    def delete_ref(
        self,
        ref_artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> None:
        ref_artifact = self.get_ref(ref_artifact_id, **kwargs)
        if ref_artifact is None:
            if raise_error:
                raise ValueError(f"Ref artifact with id '{ref_artifact_id}' not found.")

        artifact_ids = ref_artifact.artifact_ids.copy()
        for artifact_id in artifact_ids:
            self.delete(artifact_id, raise_error=False, **kwargs)

        self._kvstore.delete(ref_artifact_id, collection=self._artifact_collection, **kwargs)
        self._kvstore.delete(ref_artifact_id, collection=self._metadata_collection, **kwargs)
        self._kvstore.delete(ref_artifact_id, collection=self._ref_collection, **kwargs)

    async def adelete_ref(
        self, ref_artifact_id: str,
        raise_error: bool = True,
        **kwargs
    ) -> None:
        ref_artifact = await self.aget_ref(ref_artifact_id, **kwargs)
        if ref_artifact is None:
            if raise_error:
                raise ValueError(f"Ref artifact with id '{ref_artifact_id}' not found.")

        artifact_ids = ref_artifact.artifact_ids.copy()
        for artifact_id in artifact_ids:
            await self.adelete(artifact_id, raise_error=False, **kwargs)

        await asyncio.gather(
            self._kvstore.adelete(ref_artifact_id, collection=self._artifact_collection, **kwargs),
            self._kvstore.adelete(ref_artifact_id, collection=self._metadata_collection, **kwargs),
            self._kvstore.adelete(ref_artifact_id, collection=self._ref_collection, **kwargs)
        )