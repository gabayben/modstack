from dataclasses import dataclass, field
from typing import Optional, Sequence, override

from modstack.ai.prompts import EXTRACT_TRIPLETS_PROMPT
from modstack.artifacts import Artifact
from modstack.core import Module, ModuleLike, coerce_to_module
from modstack.data.stores import GraphStore, RefArtifactInfo
from modstack.query.indices.artifact_store import ArtifactStoreIndex
from modstack.query.structs import KnowledgeGraph, Triplet
from modstack.settings import Settings

@dataclass
class KnowledgeGraphIndex(ArtifactStoreIndex[KnowledgeGraph]):
    _graph_store: GraphStore = field(default=Settings.graph_store, kw_only=True)
    _triplet_extractor: Optional[ModuleLike[str, list[Triplet]]] = field(default=None, kw_only=True)
    _extract_triplets_template: str = field(default=EXTRACT_TRIPLETS_PROMPT, kw_only=True)

    @property
    def graph_store(self) -> GraphStore:
        return self._graph_store

    @property
    def triplet_extractor(self) -> Module[str, list[Triplet]]:
        return self._triplet_extractor

    def __post_init__(self):
        self._triplet_extractor: Module[str, list[Triplet]] = coerce_to_module(
            self._triplet_extractor or self._llm_extract_triplets
        )

    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> KnowledgeGraph:
        pass

    @override
    async def _abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> KnowledgeGraph:
        pass

    def _insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    @override
    async def _ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    def _delete(self, artifact_id: str, **kwargs) -> None:
        raise NotImplementedError('Delete is not yet supported for KnowledgeGraphIndex.')

    def get_refs(self) -> dict[str, RefArtifactInfo]:
        pass

    @override
    async def aget_refs(self) -> dict[str, RefArtifactInfo]:
        pass

    def _llm_extract_triplets(self, text: str) -> list[Triplet]:
        pass