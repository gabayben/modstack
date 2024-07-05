from typing import Sequence, override

from modstack.artifacts import Artifact
from modstack.query.indices.common import CommonIndex
from modstack.query.structs.void import VoidStruct
from modstack.stores import RefArtifactInfo

class PropertyGraphIndex(CommonIndex[VoidStruct]):
    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> VoidStruct:
        pass

    @override
    async def _abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> VoidStruct:
        pass

    def _insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    @override
    async def _ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    def _delete(self, artifact_id: str, **kwargs) -> None:
        pass

    @override
    async def _adelete(self, artifact_id: str, **kwargs) -> None:
        pass

    def get_refs(self) -> dict[str, RefArtifactInfo]:
        pass

    @override
    async def aget_refs(self) -> dict[str, RefArtifactInfo]:
        pass