from collections import defaultdict
from dataclasses import dataclass, field
import logging
from typing import Sequence

from modstack.ai import Embedder
from modstack.ai.utils import aembed_artifacts, embed_artifacts
from modstack.artifacts import Artifact, ArtifactInfo, Text
from modstack.core import coerce_to_module
from modstack.data.stores import RefArtifactInfo, VectorStore
from modstack.query.indices import Index
from modstack.query.structs import SummaryStruct
from modstack.query.synthesizers import Synthesis, Synthesizer, SynthesizerLike
from modstack.settings import Settings

logger = logging.getLogger(__name__)

DEFAULT_SUMMARY_QUERY = Text(
    "Describe what the provided text is about. "
    "Also describe some of the questions that this text can answer. "
)

@dataclass
class SummaryIndex(Index[SummaryStruct]):
    _vector_store: VectorStore = field(default=Settings.vector_store, kw_only=True)
    _embedder: Embedder = field(default=Settings.embedder, kw_only=True)
    _synthesizer: SynthesizerLike = field(kw_only=True)
    _summary_query: Artifact = field(default=DEFAULT_SUMMARY_QUERY, kw_only=True)
    _embed_summaries: bool = field(default=True, kw_only=True)

    @property
    def vector_store(self) -> VectorStore:
        return self._vector_store

    @property
    def embedder(self) -> Embedder:
        return self._embedder

    def __post_init__(self):
        self._synthesizer: Synthesizer = coerce_to_module(self._synthesizer)

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
            summary = self._synthesizer.invoke(
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
            summaries = list(ref_id_to_summary.values())
            embedded_summaries = embed_artifacts(self.embedder, summaries, **kwargs)
            self.vector_store.insert(embedded_summaries, **kwargs)

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
            summary = await self._synthesizer.ainvoke(
                Synthesis(self._summary_query, chunks),
                **kwargs
            )
            metadata = ref_id_to_chunks.get(ref_id, [Text('')])[0].metadata
            summary.metadata.update(metadata)
            summary.ref = ArtifactInfo(ref_id)
            ref_id_to_summary[ref_id] = summary
            await self.artifact_store.ainsert([summary])
            logger.info(f'> Generated summary for ref {ref_id}: {str(summary)}')

        for ref_id, chunks in ref_id_to_chunks.items():
            self.struct.add_summary_and_chunks(ref_id_to_summary[ref_id], chunks)

        if self._embed_summaries:
            summaries = list(ref_id_to_summary.values())
            embedded_summaries = await aembed_artifacts(self.embedder, summaries, **kwargs)
            await self.vector_store.ainsert(embedded_summaries, **kwargs)

    def delete_ref(self, ref_id: str, delete_from_store: bool = False, **kwargs) -> None:
        ref_info = self.artifact_store.get_ref(ref_id)
        if ref_info is None:
            logger.warning(f'ref_id {ref_id} not found, nothing deleted.')
            return
        self.struct.delete_ref(ref_id)
        self.vector_store.delete_ref(ref_id)
        if delete_from_store:
            self.artifact_store.delete_ref(ref_id, raise_error=False)
        self.index_store.upsert_struct(self.struct, **kwargs)

    def delete_many(self, artifact_ids: list[str], delete_from_store: bool = False, **kwargs) -> None:
        refs_to_remove = self._delete_chunks(artifact_ids)
        for ref_id in refs_to_remove:
            self.delete_ref(ref_id)

    async def adelete_ref(self, ref_id: str, delete_from_store: bool = False, **kwargs) -> None:
        ref_info = await self.artifact_store.aget_ref(ref_id)
        if ref_info is None:
            logger.warning(f'ref_id {ref_id} not found, nothing deleted.')
            return
        self.struct.delete_ref(ref_id)
        await self.vector_store.adelete_ref(ref_id)
        if delete_from_store:
            await self.artifact_store.adelete_ref(ref_id, raise_error=False)
        await self.index_store.aupsert_struct(self.struct, **kwargs)

    async def adelete_many(self, artifact_ids: list[str], delete_from_store: bool = False, **kwargs) -> None:
        refs_to_remove = self._delete_chunks(artifact_ids)
        for ref_id in refs_to_remove:
            await self.adelete_ref(ref_id)

    def _delete_chunks(self, artifact_ids: list[str]) -> list[str]:
        chunk_ids = self.struct.chunk_ids
        for artifact_id in artifact_ids:
            if artifact_id not in chunk_ids:
                logger.warning(f'artifact_id {artifact_id} not found, will not be deleted.')
                artifact_ids.remove(artifact_id)
        self.struct.delete_chunks(artifact_ids)

        summaries_to_remove = [
            summary_id
            for summary_id in self.struct.summary_ids
            if len(self.struct.summary_to_chunks[summary_id]) == 0
        ]

        return [
            ref_id
            for ref_id in self.struct.ref_ids
            if self.struct.ref_to_summary[ref_id] in summaries_to_remove
        ]

    def get_refs(self) -> dict[str, RefArtifactInfo]:
        ref_ids = self.struct.ref_ids
        ref_infos: dict[str, RefArtifactInfo] = {}
        for ref_id in ref_ids:
            ref_info = self.artifact_store.get_ref(ref_id)
            if not ref_info:
                continue
            ref_infos[ref_id] = ref_info
        return ref_infos

    async def aget_refs(self) -> dict[str, RefArtifactInfo]:
        ref_ids = self.struct.ref_ids
        ref_infos: dict[str, RefArtifactInfo] = {}
        for ref_id in ref_ids:
            ref_info = await self.artifact_store.aget_ref(ref_id)
            if not ref_info:
                continue
            ref_infos[ref_id] = ref_info
        return ref_infos