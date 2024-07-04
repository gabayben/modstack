from abc import ABC, abstractmethod
import asyncio
import logging
from typing import Sequence

from modstack.artifacts import Artifact
from modstack.data.stores import RefArtifactInfo
from modstack.query.indices import Index
from modstack.query.indices.base import STRUCT
from modstack.utils.threading import run_async

logger = logging.getLogger(__name__)

class SimpleIndex(Index[STRUCT], ABC):
    def _build(self, artifacts: Sequence[Artifact], **kwargs) -> STRUCT:
        self.artifact_store.insert(artifacts, allow_update=True)
        return self._build_from_artifacts(artifacts, **kwargs)

    @abstractmethod
    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> STRUCT:
        pass

    async def _abuild(self, artifacts: Sequence[Artifact], **kwargs) -> STRUCT:
        await self.artifact_store.ainsert(artifacts, allow_update=True)
        return await self._abuild_from_artifacts(artifacts, **kwargs)

    async def _abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> STRUCT:
        return await run_async(self._build_from_artifacts, artifacts, **kwargs)

    def insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        self.artifact_store.insert(artifacts, allow_update=True)
        self._insert_many(artifacts, **kwargs)
        self.index_store.upsert_struct(self.struct, **kwargs)

    @abstractmethod
    def _insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    async def ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        await self.artifact_store.ainsert(artifacts, allow_update=True)
        await self._ainsert_many(artifacts, **kwargs)
        await self.index_store.aupsert_struct(self.struct, **kwargs)

    async def _ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        await run_async(self._insert_many, artifacts, **kwargs)

    def delete_ref(
        self,
        ref_id: str,
        delete_from_store: bool = False,
        **kwargs
    ) -> None:
        ref_artifact_info = self.artifact_store.get_ref(ref_id)
        if ref_artifact_info is None:
            logger.warning(f"Ref artifact with id '{ref_id}' not found. Nothing deleted.")
            return
        self.delete_many(ref_artifact_info.artifact_ids, delete_from_store=False, **kwargs)
        if delete_from_store:
            self.artifact_store.delete_ref(ref_id, raise_error=False, **kwargs)

    def delete_many(
        self,
        artifact_ids: list[str],
        delete_from_store: bool = False,
        **kwargs
    ) -> None:
        for artifact_id in artifact_ids:
            self._delete(artifact_id, **kwargs)
            if delete_from_store:
                self.artifact_store.delete(artifact_id, raise_error=False, **kwargs)
        self.index_store.aupsert_struct(self.struct)

    @abstractmethod
    def _delete(self, artifact_id: str, **kwargs) -> None:
        pass

    async def adelete_ref(
        self,
        ref_id: str,
        delete_from_store: bool = False,
        **kwargs
    ) -> None:
        ref_artifact_info = await self.artifact_store.aget_ref(ref_id)
        if ref_artifact_info is None:
            logger.warning(f"Ref artifact with id '{ref_id}' not found. Nothing deleted.")
        await self.adelete_many(ref_artifact_info.artifact_ids, delete_from_store=False, **kwargs)
        if delete_from_store:
            await self.artifact_store.adelete_ref(ref_id, raise_error=False, **kwargs)

    async def adelete_many(
        self,
        artifact_ids: list[str],
        delete_from_store: bool = False,
        **kwargs
    ) -> None:
        async def adelete(artifact_id: str) -> None:
            await self._adelete(artifact_id, **kwargs)
            if delete_from_store:
                await self.artifact_store.adelete(artifact_id, raise_error=False, **kwargs)
        await asyncio.gather(adelete(artifact_id) for artifact_id in artifact_ids)
        await self.index_store.aupsert_struct(self.struct)

    async def _adelete(self, artifact_id: str, **kwargs) -> None:
        await run_async(self._delete, artifact_id, **kwargs)

    async def aget_refs(self) -> dict[str, RefArtifactInfo]:
        return await run_async(self.get_refs)