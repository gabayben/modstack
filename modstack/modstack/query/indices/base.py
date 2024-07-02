from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, Optional, Sequence, TypeVar

from modstack.artifacts import Artifact
from modstack.query.structs import IndexStruct
from modstack.core import ArtifactTransform
from modstack.core.utils import arun_transformations, run_transformations
from modstack.settings import Settings
from modstack.data.stores import ArtifactStore, InjestionCache, RefArtifactInfo, IndexStore

STRUCT = TypeVar('STRUCT', bound=IndexStruct)

@dataclass
class Index(Generic[STRUCT], ABC):
    _struct: Optional[STRUCT] = field(default=None, init=False)
    _index_store: IndexStore = field(default=Settings.index_store, kw_only=True)
    _artifact_store: ArtifactStore = field(default=Settings.artifact_store, kw_only=True)
    _cache: Optional[InjestionCache] = field(default=Settings.ingestion_cache, kw_only=True)
    _cache_collection: Optional[str] = field(default=None, kw_only=True)
    _transformations: list[ArtifactTransform] = field(default_factory=list, kw_only=True)

    @property
    def struct(self) -> STRUCT:
        if not self.is_built:
            raise ValueError(
                f'Index not built. Call {self.__class__.__name__}.build(...) before accessing struct.'
            )
        return self._struct

    @property
    def index_store(self) -> IndexStore:
        return self._index_store

    @property
    def artifact_store(self) -> ArtifactStore:
        raise self._artifact_store

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
            struct = self.build_from_artifacts(artifacts, **kwargs)
        self._struct = struct
        self.index_store.upsert_struct(self.struct, **kwargs)

    @abstractmethod
    def build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> STRUCT:
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
            struct = await self.build_from_artifacts(artifacts, **kwargs)
        self._struct = struct
        await self.index_store.aupsert_struct(self.struct, **kwargs)

    @abstractmethod
    async def abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> STRUCT:
        pass

    def insert_ref(self, ref: Artifact, **kwargs) -> None:
        artifacts = (
            run_transformations(
                [ref],
                self.transformations,
                cache=self.cache,
                cache_collection=self.cache_collection
            )
            if self.transformations
            else [ref]
        )
        self.insert_many(artifacts, **kwargs)
        self.artifact_store.set_hash(ref.id, ref.get_hash())

    @abstractmethod
    def insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    async def ainsert_ref(self, ref: Artifact, **kwargs) -> None:
        artifacts = (
            await arun_transformations(
                [ref],
                self.transformations,
                cache=self.cache,
                cache_collection=self.cache_collection
            )
            if self.transformations
            else [ref]
        )
        await self.ainsert_many(artifacts, **kwargs)
        await self.artifact_store.aset_hash(ref.id, ref.get_hash())

    @abstractmethod
    async def ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    def update_ref(
        self,
        ref: Artifact,
        delete_kwargs: dict[str, Any] = {},
        insert_kwargs: dict[str, Any] = {}
    ) -> None:
        self.delete_ref(ref.id, delete_from_store=True, **delete_kwargs)
        self.insert_ref(ref, **insert_kwargs)

    async def aupdate_ref(
        self,
        ref: Artifact,
        delete_kwargs: dict[str, Any] = {},
        insert_kwargs: dict[str, Any] = {}
    ) -> None:
        await self.adelete_ref(ref.id, delete_from_store=True, **delete_kwargs)
        await self.ainsert_ref(ref, **insert_kwargs)

    @abstractmethod
    def delete_ref(
        self,
        ref_id: str,
        delete_from_store: bool = False,
        **kwargs
    ) -> None:
        pass

    @abstractmethod
    def delete_many(
        self,
        artifact_ids: list[str],
        delete_from_store: bool = False,
        **kwargs
    ) -> None:
        pass

    @abstractmethod
    async def adelete_ref(
        self,
        ref_id: str,
        delete_from_store: bool = False,
        **kwargs
    ) -> None:
        pass

    @abstractmethod
    async def adelete_many(
        self,
        artifact_ids: list[str],
        delete_from_store: bool = False,
        **kwargs
    ) -> None:
        pass

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
                self.insert_ref(ref_artifact, **insert_kwargs)
                refreshed_artifacts[i] = True
            elif hash_ != ref_artifact.get_hash():
                self.update_ref(
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
                await self.ainsert_ref(ref_artifact, **insert_kwargs)
                refreshed_artifacts[i] = True
            elif hash_ != ref_artifact.get_hash():
                await self.aupdate_ref(
                    ref_artifact,
                    delete_kwargs=delete_kwargs,
                    insert_kwargs=insert_kwargs
                )
                refreshed_artifacts[i] = True
        return refreshed_artifacts

    @abstractmethod
    def get_refs(self) -> dict[str, RefArtifactInfo]:
        pass

    @abstractmethod
    async def aget_refs(self) -> dict[str, RefArtifactInfo]:
        pass