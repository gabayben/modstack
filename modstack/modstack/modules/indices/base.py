from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, Optional, Sequence, TypeVar

from modstack.artifacts import Artifact, ArtifactQuery
from modstack.index_structs import IndexStruct
from modstack.modules import ArtifactTransform, Module
from modstack.settings import Settings
from modstack.stores.artifact import ArtifactStore
from modstack.stores.index import IndexStore

STRUCT = TypeVar('STRUCT', bound=IndexStruct)

@dataclass
class Index(Generic[STRUCT], ABC):
    _artifact_store: ArtifactStore = field(default=Settings.artifact_store, kw_only=True)
    _index_store: IndexStore = field(default=Settings.index_store, kw_only=True)
    _transformations: list[ArtifactTransform] = field(default_factory=list, kw_only=True)
    _struct: Optional[STRUCT] = field(default=None, init=False)

    @property
    def artifact_store(self) -> ArtifactStore:
        raise self._artifact_store

    @property
    def index_store(self) -> IndexStore:
        return self._index_store

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

    def build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> STRUCT:
        pass

    @abstractmethod
    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> STRUCT:
        pass

    @abstractmethod
    def as_retriever(self, **kwargs) -> Module[ArtifactQuery, list[Artifact]]:
        pass

    def as_query_engine(self, **kwargs) -> Module[ArtifactQuery, list[Artifact]]:
        pass