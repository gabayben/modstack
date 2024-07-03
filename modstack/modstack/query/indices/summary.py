from collections import defaultdict
from dataclasses import dataclass, field
import logging
from typing import Sequence

from modstack.artifacts import Artifact, ArtifactInfo, ArtifactRelationship, Text
from modstack.data.stores import RefArtifactInfo, VectorStore
from modstack.query.indices import Index
from modstack.query.structs import SummaryStruct
from modstack.query.synthesizers import Synthesis, Synthesizer
from modstack.settings import Settings

logger = logging.getLogger(__name__)

DEFAULT_SUMMARY_QUERY = Text(
    "Describe what the provided text is about. "
    "Also describe some of the questions that this text can answer. "
)

@dataclass
class SummaryIndex(Index[SummaryStruct]):
    _vector_store: VectorStore = field(default=Settings.vector_store, kw_only=True)
    _synthesizer: Synthesizer = field(kw_only=True)
    _summary_query: Artifact = field(default=DEFAULT_SUMMARY_QUERY, kw_only=True)
    _embed_summaries: bool = field(default=True, kw_only=True)

    @property
    def vector_store(self) -> VectorStore:
        return self._vector_store

    @property
    def synthesizer(self) -> Synthesizer:
        return self._synthesizer

    def _build(self, artifacts: Sequence[Artifact], **kwargs) -> SummaryStruct:
        self.artifact_store.insert(artifacts, **kwargs)
        struct = SummaryStruct()
        self._insert_artifacts_to_index(struct, list(artifacts), **kwargs)
        return struct

    async def _abuild(self, artifacts: Sequence[Artifact], **kwargs) -> SummaryStruct:
        await self.artifact_store.ainsert(artifacts, **kwargs)
        struct = SummaryStruct()
        await self._ainsert_artifacts_to_index(struct, list(artifacts), **kwargs)
        return struct

    def insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        self.artifact_store.insert(artifacts, allow_update=True)
        self._insert_artifacts_to_index(self.struct, artifacts, **kwargs)
        self.index_store.upsert_struct(self.struct, **kwargs)

    def _insert_artifacts_to_index(
        self,
        struct: SummaryStruct,
        artifacts: list[Artifact],
        **kwargs
    ) -> None:
        ref_id_to_chunks: dict[str, list[Artifact]] = defaultdict(list)
        ref_id_to_summary: dict[str, Artifact] = {}

        for artifact in artifacts:
            if artifact.ref is None:
                raise ValueError(
                    'ref of artifact cannot be None when building a summary index.'
                )
            ref_id_to_chunks[artifact.ref.id].append(artifact)

        for ref_id, chunks in ref_id_to_chunks.items():
            logger.info(f'Current ref id: {ref_id}')
            summary = self.synthesizer.invoke(
                Synthesis(self._summary_query, chunks),
                **kwargs
            )
            metadata = ref_id_to_chunks.get(ref_id, [Text('')])[0].metadata
            summary.metadata.update(metadata)
            summary.ref = ArtifactInfo(ref_id)
            ref_id_to_summary[ref_id] = summary
            self.artifact_store.insert([summary])
            logger.info(f'> Generated summary for ref {ref_id}: {str(summary)}')

        for ref_id, chunks in ref_id_to_chunks.items():
            self.struct.add_summary_and_chunks(ref_id_to_summary[ref_id], chunks)

        if self._embed_summaries:
            pass

    async def ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        await self.artifact_store.ainsert(artifacts, allow_update=True)
        await self._ainsert_artifacts_to_index(self.struct, artifacts, **kwargs)
        await self.index_store.aupsert_struct(self.struct, **kwargs)

    async def _ainsert_artifacts_to_index(
        self,
        struct: SummaryStruct,
        artifacts: list[Artifact],
        **kwargs
    ) -> None:
        pass

    def delete_ref(self, ref_id: str, delete_from_store: bool = False, **kwargs) -> None:
        pass

    def delete_many(self, artifact_ids: list[str], delete_from_store: bool = False, **kwargs) -> None:
        pass

    async def adelete_ref(self, ref_id: str, delete_from_store: bool = False, **kwargs) -> None:
        pass

    async def adelete_many(self, artifact_ids: list[str], delete_from_store: bool = False, **kwargs) -> None:
        pass

    def get_refs(self) -> dict[str, RefArtifactInfo]:
        pass

    async def aget_refs(self) -> dict[str, RefArtifactInfo]:
        pass