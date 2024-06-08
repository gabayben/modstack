from typing import Sequence

from modstack.artifacts import Artifact
from modstack.indices import Index
from modstack.indices.structs import ListIndexStruct
from modstack.stores.artifact import RefArtifactInfo

class ListIndex(Index[ListIndexStruct]):
    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> ListIndexStruct:
        pass

    async def _abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> ListIndexStruct:
        return self._build_from_artifacts(artifacts, **kwargs)

    def get_ref_artifacts(self) -> dict[str, RefArtifactInfo]:
        pass

    async def aget_ref_artifacts(self) -> dict[str, RefArtifactInfo]:
        pass

    def _insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    async def _ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    def _delete(self, artifact_id: str, **kwargs) -> None:
        pass

    async def _adelete(self, artifact_id: str, **kwargs) -> None:
        pass