from typing import Sequence, override

from modstack.artifacts import Artifact
from modstack.data.stores import RefArtifactInfo
from modstack.query.indices.artifact_store import ArtifactStoreIndex
from modstack.query.structs import ListStruct

class ListIndex(ArtifactStoreIndex[ListStruct]):
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

    def get_refs(self) -> dict[str, RefArtifactInfo]:
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

    @override
    async def aget_refs(self) -> dict[str, RefArtifactInfo]:
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