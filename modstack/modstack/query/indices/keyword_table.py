from dataclasses import dataclass, field
from typing import Sequence, override

from modstack.artifacts import Artifact
from modstack.core import Module, ModuleLike, coerce_to_module
from modstack.stores import RefArtifactInfo
from modstack.query.helpers import simple_keyword_extractor
from modstack.query.indices.simple import SimpleIndex
from modstack.query.structs import KeywordTable

@dataclass
class KeywordTableIndex(SimpleIndex[KeywordTable]):
    _keyword_extractor: ModuleLike[Artifact, set[str]] = field(default=simple_keyword_extractor, kw_only=True)

    @property
    def keyword_extractor(self) -> Module[Artifact, set[str]]:
        return self._keyword_extractor

    def __post_init__(self):
        self._keyword_extractor: Module[Artifact, set[str]] = coerce_to_module(self._keyword_extractor)

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