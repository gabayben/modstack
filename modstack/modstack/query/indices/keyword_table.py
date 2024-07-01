from dataclasses import dataclass, field
from typing import Sequence

from modstack.artifacts import Artifact
from modstack.core import Module, ModuleLike, coerce_to_module
from modstack.data.stores import RefArtifactInfo
from modstack.query.common import simple_keyword_extractor
from modstack.query.indices import Index
from modstack.query.structs import KeywordTable

@dataclass
class KeywordTableIndex(Index[KeywordTable]):
    _keyword_extractor: ModuleLike[Artifact, set[str]] = field(default=simple_keyword_extractor, kw_only=True)
    keyword_extractor: Module[Artifact, set[str]]

    def __post_init__(self):
        self.keyword_extractor = coerce_to_module(self._keyword_extractor)

    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> KeywordTable:
        pass

    async def _abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> KeywordTable:
        pass

    def get_ref_artifacts(self) -> dict[str, RefArtifactInfo]:
        pass

    async def aget_ref_artifacts(self) -> dict[str, RefArtifactInfo]:
        pass

    def _insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    async def _ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    def _delete(self, artifact_id: str, **kwargs) -> None:
        pass

    async def _adelete(self, artifact_id: str, **kwargs) -> None:
        pass