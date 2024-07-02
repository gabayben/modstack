from modstack.query.structs import IndexStruct

class SummaryStruct(IndexStruct):
    summary_to_chunks: dict[str, list[str]]
    chunk_to_summary: dict[str, str]
    document_to_summary: dict[str, str]

    @property
    def summary_ids(self) -> list[str]:
        return list(self.summary_to_chunks.keys())

    @property
    def chunk_ids(self) -> list[str]:
        return list(self.chunk_to_summary.keys())

    @property
    def document_ids(self) -> list[str]:
        return list(self.document_to_summary.keys())