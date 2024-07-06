from dataclasses import dataclass, field
from typing import Optional, Sequence, Unpack, override

from modstack.artifacts import Artifact
from modstack.core import Module, ModuleLike, coerce_to_module
from modstack.query.indices import IndexData, Indexer
from modstack.query.indices.base import IndexDependencies
from modstack.stores import RefArtifactInfo
from modstack.query.helpers import simple_keyword_extractor
from modstack.query.indices.common import CommonIndex
from modstack.query.structs import KeywordTable

class KeywordTableIndexDependencies(IndexDependencies, total=False):
    keyword_extractor: Optional[ModuleLike[Artifact, set[str]]]

@dataclass(kw_only=True)
class KeywordTableIndex(CommonIndex[KeywordTable]):
    keyword_extractor: Optional[ModuleLike[Artifact, set[str]]] = field(default=None)

    def __post_init__(self):
        super().__post_init__()
        self.keyword_extractor: Module[Artifact, set[str]] = (
            coerce_to_module(self.keyword_extractor)
            if self.keyword_extractor
            else simple_keyword_extractor
        )

    @classmethod
    def indexer(cls, **kwargs: Unpack[KeywordTableIndexDependencies]) -> Module[IndexData[KeywordTable], 'KeywordTableIndex']:
        return Indexer(cls(**kwargs))

    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> KeywordTable:
        struct = KeywordTable()
        self._insert_artifacts_to_index(struct, list(artifacts), **kwargs)
        return struct

    @override
    async def _abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> KeywordTable:
        struct = KeywordTable()
        await self._ainsert_artifacts_to_index(struct, list(artifacts), **kwargs)
        return struct

    def _insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        self._insert_artifacts_to_index(self.struct, artifacts, **kwargs)

    def _insert_artifacts_to_index(
        self,
        struct: KeywordTable,
        artifacts: list[Artifact],
        **kwargs
    ) -> None:
        for artifact in artifacts:
            keywords = self.keyword_extractor.invoke(artifact, **kwargs)
            struct.add_artifact(artifact, keywords)

    @override
    async def _ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        await self._ainsert_artifacts_to_index(self.struct, artifacts, **kwargs)

    async def _ainsert_artifacts_to_index(
        self,
        struct: KeywordTable,
        artifacts: list[Artifact],
        **kwargs
    ) -> None:
        for artifact in artifacts:
            keywords = await self.keyword_extractor.ainvoke(artifact, **kwargs)
            struct.add_artifact(artifact, keywords)

    def _delete(self, artifact_id: str, **kwargs) -> None:
        keywords_to_delete = set()
        for keyword, artifact_ids in self.struct.table.items():
            if artifact_id in artifact_ids:
                artifact_ids.remove(artifact_id)
                if len(artifact_ids) == 0:
                    keywords_to_delete.add(keyword)
        for keyword in keywords_to_delete:
            del self.struct.table[keyword]

    def get_refs(self) -> dict[str, RefArtifactInfo]:
        artifacts = self.artifact_store.get_many(list(self.struct.artifact_ids))
        ref_infos: dict[str, RefArtifactInfo] = {}
        for artifact in artifacts:
            ref = artifact.ref
            if not ref:
                continue
            ref_info = self.artifact_store.get_ref(ref.id)
            if not ref_info:
                continue
            ref_infos[ref.id] = ref_info
        return ref_infos

    @override
    async def aget_refs(self) -> dict[str, RefArtifactInfo]:
        artifacts = await self.artifact_store.aget_many(list(self.struct.artifact_ids))
        ref_infos: dict[str, RefArtifactInfo] = {}
        for artifact in artifacts:
            ref = artifact.ref
            if not ref:
                continue
            ref_info = await self.artifact_store.aget_ref(ref.id)
            if not ref_info:
                continue
            ref_infos[ref.id] = ref_info
        return ref_infos