from typing import Sequence

from modstack.artifacts import Artifact
from modstack.indices import Index
from modstack.indices.structs import ListIndexStruct
from modstack.stores.artifact import RefArtifactInfo

class ListIndex(Index[ListIndexStruct]):
    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> ListIndexStruct:
        struct = ListIndexStruct()
        for artifact in artifacts:
            struct.add_artifact(artifact.id)
        return struct

    async def _abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> ListIndexStruct:
        return self._build_from_artifacts(artifacts, **kwargs)

    def get_ref_artifacts(self) -> dict[str, RefArtifactInfo]:
        artifacts = self.artifact_store.get_many(self.struct.artifact_ids)
        ref_artifacts: dict[str, RefArtifactInfo] = {}
        for artifact in artifacts:
            ref = artifact.ref
            if ref is None:
                continue
            ref_artifact = self.artifact_store.get_ref(ref.id)
            if ref_artifact is None:
                continue
            ref_artifacts[ref.id] = ref_artifact
        return ref_artifacts

    async def aget_ref_artifacts(self) -> dict[str, RefArtifactInfo]:
        artifacts = await self.artifact_store.aget_many(self.struct.artifact_ids)
        ref_artifacts: dict[str, RefArtifactInfo] = {}
        for artifact in artifacts:
            ref = artifact.ref
            if ref is None:
                continue
            ref_artifact = await self.artifact_store.aget_ref(ref.id)
            if ref_artifact is None:
                continue
            ref_artifacts[ref.id] = ref_artifact
        return ref_artifacts

    def _insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        for artifact in artifacts:
            self.struct.add_artifact(artifact.id)

    async def _ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        self._insert_many(artifacts, **kwargs)

    def _delete(self, artifact_id: str, **kwargs) -> None:
        artifacts = self.artifact_store.get_many(self.struct.artifact_ids, **kwargs)
        artifacts_to_keep = [artifact for artifact in artifacts if artifact.id != artifact_id]
        self.struct.artifact_ids = artifacts_to_keep

    async def _adelete(self, artifact_id: str, **kwargs) -> None:
        artifacts = await self.artifact_store.aget_many(self.struct.artifact_ids, **kwargs)
        artifacts_to_keep = [artifact for artifact in artifacts if artifact.id != artifact_id]
        self.struct.artifact_ids = artifacts_to_keep