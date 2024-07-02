from typing import Union

from modstack.artifacts import Artifact
from modstack.query.structs import IndexStruct

class SummaryStruct(IndexStruct):
    summary_to_chunks: dict[str, set[str]]
    chunk_to_summary: dict[str, str]
    ref_to_summary: dict[str, str]

    @property
    def summary_ids(self) -> list[str]:
        return list(self.summary_to_chunks.keys())

    @property
    def chunk_ids(self) -> list[str]:
        return list(self.chunk_to_summary.keys())

    @property
    def ref_ids(self) -> list[str]:
        return list(self.ref_to_summary.keys())

    def add_summary_and_chunks(
        self,
        summary: Artifact,
        chunks: list[Union[str, Artifact]]
    ) -> None:
        if summary.ref is None:
            raise ValueError('ref of summary cannot be None when building a SummaryStruct.')

        summary_id = summary.id
        ref_id = summary.ref.id
        self.ref_to_summary[ref_id] = summary_id

        for chunk in chunks:
            chunk_id = chunk if isinstance(chunk, str) else chunk.id
            if summary_id not in self.summary_to_chunks:
                self.summary_to_chunks[summary_id] = set()
            self.summary_to_chunks[summary_id].add(chunk_id)
            self.chunk_to_summary[chunk_id] = summary_id

    def delete_ref(self, ref_id: str) -> None:
        summary_id = self.ref_to_summary[ref_id]
        del self.ref_to_summary[ref_id]
        chunk_ids = self.summary_to_chunks[summary_id]
        for chunk_id in chunk_ids:
            del self.chunk_to_summary[chunk_id]
        del self.summary_to_chunks[summary_id]

    def delete_chunks(self, chunk_ids: list[str]) -> None:
        for chunk_id in chunk_ids:
            summary_id = self.chunk_to_summary[chunk_id]
            self.summary_to_chunks[summary_id].remove(chunk_id)
            del self.chunk_to_summary[chunk_id]