from abc import ABC
from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar

from modstack.artifacts import Artifact
from modstack.index_structs import IndexStruct
from modstack.modules import ArtifactTransform
from modstack.settings import Settings
from modstack.stores.artifact import ArtifactStore
from modstack.stores.index import IndexStore

STRUCT = TypeVar('STRUCT', bound=IndexStruct)

@dataclass
class Index(Generic[STRUCT], ABC):
    _artifact_store: ArtifactStore = field(default=Settings.artifact_store, kw_only=True)
    _index_store: IndexStore = field(default=Settings.index_store, kw_only=True)
    _transformations: list[ArtifactTransform] = field(default_factory=list, kw_only=True)

    @property
    def artifact_store(self) -> ArtifactStore:
        return self._artifact_store

    @property
    def index_store(self) -> IndexStore:
        return self._index_store

    def build(
        self,
        struct: Optional[STRUCT] = None,
        artifacts: Optional[list[Artifact]] = None
    ):
        pass