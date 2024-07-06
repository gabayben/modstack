from typing import Sequence, Unpack, override

from modstack.artifacts import Artifact
from modstack.core import Module
from modstack.query.indices import IndexData, Indexer
from modstack.query.indices.base import IndexDependencies
from modstack.query.indices.common import CommonIndex
from modstack.query.structs import ListStruct

class ListIndex(CommonIndex[ListStruct]):
    @classmethod
    def indexer(cls, **kwargs: Unpack[IndexDependencies]) -> Module[IndexData[ListStruct], 'ListIndex']:
        return Indexer(cls(**kwargs))

    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> ListStruct:
        struct = ListStruct()
        for artifact in artifacts:
            struct.add_artifact(artifact.id)
        return struct

    def _insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        for artifact in artifacts:
            self.struct.add_artifact(artifact.id)

    def _delete(self, artifact_id: str, **kwargs) -> None:
        artifacts = self.artifact_store.get_many(self.struct.artifact_ids, **kwargs)
        artifacts_to_keep = [artifact for artifact in artifacts if artifact.id != artifact_id]
        self.struct.artifact_ids = artifacts_to_keep

    @override
    async def _adelete(self, artifact_id: str, **kwargs) -> None:
        artifacts = await self.artifact_store.aget_many(self.struct.artifact_ids, **kwargs)
        artifacts_to_keep = [artifact for artifact in artifacts if artifact.id != artifact_id]
        self.struct.artifact_ids = artifacts_to_keep

    def get_ref_ids(self) -> list[str]:
        return []

    def get_artifact_ids(self) -> list[str]:
        return self.struct.artifact_ids