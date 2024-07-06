from dataclasses import dataclass, field
from typing import Sequence, Unpack, override

from modstack.artifacts import Artifact
from modstack.config import Settings
from modstack.core import Module
from modstack.query.indices import IndexData, Indexer
from modstack.query.indices.base import IndexDependencies
from modstack.query.indices.common import CommonIndex
from modstack.query.structs.void import VoidStruct
from modstack.stores import GraphStore, RefArtifactInfo

class PropertyGraphIndexDependencies(IndexDependencies, total=False):
    graph_store: GraphStore

@dataclass
class PropertyGraphIndex(CommonIndex[VoidStruct]):
    graph_store: GraphStore = field(default=Settings.graph_store, kw_only=True)

    @classmethod
    def indexer(cls, **kwargs: Unpack[PropertyGraphIndexDependencies]) -> Module[IndexData[VoidStruct], 'PropertyGraphIndex']:
        return Indexer(cls(**kwargs))

    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> VoidStruct:
        pass

    @override
    async def _abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> VoidStruct:
        pass

    def _insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    @override
    async def _ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    def _delete(self, artifact_id: str, **kwargs) -> None:
        pass

    @override
    async def _adelete(self, artifact_id: str, **kwargs) -> None:
        pass

    def get_refs(self) -> dict[str, RefArtifactInfo]:
        pass

    @override
    async def aget_refs(self) -> dict[str, RefArtifactInfo]:
        pass