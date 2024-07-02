from dataclasses import dataclass, field
from typing import Sequence

from modstack.artifacts import Artifact
from modstack.data.stores import RefArtifactInfo, VectorStore
from modstack.query.indices import Index
from modstack.query.structs import SummaryStruct
from modstack.settings import Settings

@dataclass
class SummaryIndex(Index[SummaryStruct]):
    _vector_store: VectorStore = field(default=Settings.vector_store, kw_only=True)

    @property
    def vector_store(self) -> VectorStore:
        return self._vector_store

    def build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> SummaryStruct:
        self.artifact_store.insert(artifacts, **kwargs)
        struct = SummaryStruct()
        self._insert_artifacts_to_index(struct, list(artifacts), **kwargs)
        return struct

    async def abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> SummaryStruct:
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