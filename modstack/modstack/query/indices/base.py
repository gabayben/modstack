from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass, field
import logging
from typing import Any, Generic, Optional, Sequence, TypeVar

from modstack.artifacts import Artifact
from modstack.query.structs import IndexStruct
from modstack.core import ArtifactTransform
from modstack.core.utils import arun_transformations, run_transformations
from modstack.settings import Settings
from modstack.data.stores import ArtifactStore, InjestionCache, RefArtifactInfo, IndexStore
from modstack.utils.threading import run_async

logger = logging.getLogger(__name__)

STRUCT = TypeVar('STRUCT', bound=IndexStruct)

@dataclass
class Index(Generic[STRUCT], ABC):
    _artifact_store: ArtifactStore = field(default=Settings.artifact_store, kw_only=True)
    _index_store: IndexStore = field(default=Settings.index_store, kw_only=True)
    _cache: Optional[InjestionCache] = field(default=None, kw_only=True)
    _cache_collection: Optional[str] = field(default=None, kw_only=True)
    _transformations: list[ArtifactTransform] = field(default_factory=list, kw_only=True)
    _struct: Optional[STRUCT] = field(default=None, init=False)

    @property
    def artifact_store(self) -> ArtifactStore:
        raise self._artifact_store

    @property
    def index_store(self) -> IndexStore:
        return self._index_store

    @property
    def cache(self) -> Optional[InjestionCache]:
        return self._cache

    @property
    def cache_collection(self) -> Optional[str]:
        return self._cache_collection

    @property
    def transformations(self) -> list[ArtifactTransform]:
        return self._transformations

    @property
    def struct(self) -> STRUCT:
        if not self.is_built:
            raise ValueError(
                f'Index not built. Call {self.__class__.__name__}.build(...) before accessing struct.'
            )
        return self._struct

    @property
    def is_built(self) -> bool:
        return self._struct is not None

    def build(
        self,
        struct: Optional[STRUCT] = None,
        artifacts: Optional[Sequence[Artifact]] = None,
        **kwargs
    ) -> None:
        if struct is None and artifacts is None:
            raise ValueError('Either struct or artifacts must be set.')
        if struct is not None and artifacts is not None:
            raise ValueError('struct and artifacts cannot both be set.')
        if artifacts is not None:
            self.artifact_store.insert(artifacts, allow_update=True)
            struct = self._build_from_artifacts(artifacts, **kwargs)
        self._struct = struct
        self.index_store.upsert_struct(self._struct, **kwargs)

    @abstractmethod
    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> STRUCT:
        pass

    async def abuild(
        self,
        struct: Optional[STRUCT] = None,
        artifacts: Optional[Sequence[Artifact]] = None,
        **kwargs
    ) -> None:
        if struct is None and artifacts is None:
            raise ValueError('Either struct or artifacts must be set.')
        if struct is not None and artifacts is not None:
            raise ValueError('struct and artifacts cannot both be set.')
        if artifacts is not None:
            await self.artifact_store.ainsert(artifacts, allow_update=True)
            struct = await self._abuild_from_artifacts(artifacts, **kwargs)
        self._struct = struct
        await self.index_store.aupsert_struct(self._struct, **kwargs)

    async def _abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> STRUCT:
        return await run_async(self._build_from_artifacts, artifacts, **kwargs)

    def insert(self, ref_artifact: Artifact, **kwargs) -> None:
        artifacts = (
            run_transformations(
                [ref_artifact],
                self.transformations,
                cache=self.cache,
                cache_collection=self.cache_collection
            )
            if self.transformations
            else [ref_artifact]
        )
        self.insert_many(artifacts, **kwargs)
        self.artifact_store.set_hash(ref_artifact.id, ref_artifact.get_hash())

    def insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        self.artifact_store.insert(artifacts, allow_update=True)
        self._insert_many(artifacts, **kwargs)
        self.index_store.upsert_struct(self.struct, **kwargs)

    @abstractmethod
    def _insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    async def ainsert(self, ref_artifact: Artifact, **kwargs) -> None:
        artifacts = (
            await arun_transformations(
                [ref_artifact],
                self.transformations,
                cache=self.cache,
                cache_collection=self.cache_collection
            )
            if self.transformations
            else [ref_artifact]
        )
        await self.ainsert_many(artifacts, **kwargs)
        await self.artifact_store.aset_hash(ref_artifact.id, ref_artifact.get_hash())

    async def ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        await self.artifact_store.ainsert(artifacts, allow_update=True)
        await self._ainsert_many(artifacts, **kwargs)
        await self.index_store.aupsert_struct(self.struct, **kwargs)

    async def _ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        await run_async(self._insert_many, artifacts, **kwargs)

    def update(
        self,
        ref_artifact: Artifact,
        delete_kwargs: dict[str, Any] = {},
        insert_kwargs: dict[str, Any] = {}
    ) -> None:
        self.delete(ref_artifact.id, delete_from_store=True, **delete_kwargs)
        self.insert(ref_artifact, **insert_kwargs)

    async def aupdate(
        self,
        ref_artifact: Artifact,
        delete_kwargs: dict[str, Any] = {},
        insert_kwargs: dict[str, Any] = {}
    ) -> None:
        await self.adelete(ref_artifact.id, delete_from_store=True, **delete_kwargs)
        await self.ainsert(ref_artifact, **insert_kwargs)

    def delete(
        self,
        ref_artifact_id: str,
        delete_from_store: bool = False,
        **kwargs
    ) -> None:
        ref_artifact_info = self.artifact_store.get_ref(ref_artifact_id)
        if ref_artifact_info is None:
            logger.warning(f"Ref artifact with id '{ref_artifact_id}' not found. Nothing deleted.")
            return
        self.delete_many(ref_artifact_info.artifact_ids, delete_from_store=False, **kwargs)
        if delete_from_store:
            self.artifact_store.delete_ref(ref_artifact_id, raise_error=False, **kwargs)

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

    async def adelete(
        self,
        ref_artifact_id: str,
        delete_from_store: bool = False,
        **kwargs
    ) -> None:
        ref_artifact_info = await self.artifact_store.aget_ref(ref_artifact_id)
        if ref_artifact_info is None:
            logger.warning(f"Ref artifact with id '{ref_artifact_id}' not found. Nothing deleted.")
        await self.adelete_many(ref_artifact_info.artifact_ids, delete_from_store=False, **kwargs)
        if delete_from_store:
            await self.artifact_store.adelete_ref(ref_artifact_id, raise_error=False, **kwargs)

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

    def refresh(
        self,
        ref_artifacts: list[Artifact],
        insert_kwargs: dict[str, Any] = {},
        update_kwargs: dict[str, Any] = {},
        delete_kwargs: dict[str, Any] = {}
    ) -> list[bool]:
        refreshed_artifacts = [False] * len(ref_artifacts)
        for i, ref_artifact in enumerate(ref_artifacts):
            hash_ = self.artifact_store.get_hash(ref_artifact.id)
            if hash_ is None:
                self.insert(ref_artifact, **insert_kwargs)
                refreshed_artifacts[i] = True
            elif hash_ != ref_artifact.get_hash():
                self.update(
                    ref_artifact,
                    delete_kwargs=delete_kwargs,
                    insert_kwargs=insert_kwargs
                )
                refreshed_artifacts[i] = True
        return refreshed_artifacts

    async def arefresh(
        self,
        ref_artifacts: list[Artifact],
        insert_kwargs: dict[str, Any] = {},
        update_kwargs: dict[str, Any] = {},
        delete_kwargs: dict[str, Any] = {}
    ) -> list[bool]:
        refreshed_artifacts = [False] * len(ref_artifacts)
        for i, ref_artifact in enumerate(ref_artifacts):
            hash_ = await self.artifact_store.aget_hash(ref_artifact.id)
            if hash_ is None:
                await self.ainsert(ref_artifact, **insert_kwargs)
                refreshed_artifacts[i] = True
            elif hash_ != ref_artifact.get_hash():
                await self.aupdate(
                    ref_artifact,
                    delete_kwargs=delete_kwargs,
                    insert_kwargs=insert_kwargs
                )
                refreshed_artifacts[i] = True
        return refreshed_artifacts

    @abstractmethod
    def get_ref_artifacts(self) -> dict[str, RefArtifactInfo]:
        pass

    async def aget_ref_artifacts(self) -> dict[str, RefArtifactInfo]:
        return await run_async(self.get_ref_artifacts)