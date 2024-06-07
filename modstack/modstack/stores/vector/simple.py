from dataclasses import dataclass, field
from typing import Any, Optional

from dataclasses_json import DataClassJsonMixin

from modstack.artifacts import Artifact
from modstack.stores.vector import VectorStore, VectorStoreQuery, VectorStoreQueryResult
from modstack.typing import Embedding, MetadataFilters

@dataclass
class SimpleVectorStoreData(DataClassJsonMixin):
    embeddings: dict[str, Embedding] = field(default_factory=dict)
    ref_id_mapping: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

class SimpleVectorStore(VectorStore):
    def __init__(self, data: Optional[SimpleVectorStoreData] = None):
        self._data: SimpleVectorStoreData = data or SimpleVectorStoreData()

    def retrieve(self, query: VectorStoreQuery, **kwargs) -> VectorStoreQueryResult:
        pass

    async def aretrieve(self, query: VectorStoreQuery, **kwargs) -> VectorStoreQueryResult:
        pass

    def insert(self, artifacts: list[Artifact], **kwargs) -> list[str]:
        pass

    async def ainsert(self, artifacts: list[Artifact], **kwargs) -> list[str]:
        pass

    def delete(
        self,
        artifact_ids: Optional[list[str]] = None,
        filters: Optional[MetadataFilters] = None,
        **kwargs
    ) -> None:
        pass

    async def adelete(
        self,
        artifact_ids: Optional[list[str]] = None,
        filters: Optional[MetadataFilters] = None,
        **kwargs
    ) -> None:
        pass

    def delete_ref(self, ref_artifact_id: str, **kwargs) -> None:
        pass

    async def adelete_ref(self, ref_artifact_id: str, **kwargs) -> None:
        pass

    def clear(self, **kwargs) -> None:
        pass

    async def aclear(self, **kwargs) -> None:
        pass