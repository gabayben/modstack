from typing import Sequence, override

from modstack.artifacts import Artifact
from modstack.data.stores import RefArtifactInfo
from modstack.query.indices import Index
from modstack.query.structs import SummaryStruct

class SummaryIndex(Index[SummaryStruct]):
    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> SummaryStruct:
        pass

    @override
    async def _abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> SummaryStruct:
        pass

    def _insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    def _insert_artifacts_to_index(
        self,
        struct: SummaryStruct,
        artifacts: list[Artifact],
        **kwargs
    ) -> None:
        pass

    @override
    async def _ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    async def _ainsert_artifacts_to_index(
        self,
        struct: SummaryStruct,
        artifacts: list[Artifact],
        **kwargs
    ) -> None:
        pass

    @override
    def delete(
        self,
        ref_artifact_id: str,
        delete_from_store: bool = False,
        **kwargs
    ) -> None:
        pass

    @override
    def delete_many(
        self,
        artifact_ids: list[str],
        delete_from_store: bool = False,
        **kwargs
    ) -> None:
        pass

    def _delete(self, artifact_id: str, **kwargs) -> None:
        pass

    @override
    async def adelete(
        self,
        ref_artifact_id: str,
        delete_from_store: bool = False,
        **kwargs
    ) -> None:
        pass

    @override
    async def adelete_many(
        self,
        artifact_ids: list[str],
        delete_from_store: bool = False,
        **kwargs
    ) -> None:
        pass

    def get_ref_artifacts(self) -> dict[str, RefArtifactInfo]:
        pass