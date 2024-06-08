from typing import overload

from pydantic import PrivateAttr

from modstack.artifacts import Artifact
from modstack.indices.structs import IndexStruct

class ListStruct(IndexStruct):
    _artifact_ids: list[str] = PrivateAttr(default_factory=list)

    @property
    def artifact_ids(self) -> list[str]:
        return self._artifact_ids

    @artifact_ids.setter
    @overload
    def artifact_ids(self, artifact_ids: list[str]) -> None:
        self._artifact_ids = artifact_ids

    @artifact_ids.setter
    def artifact_ids(self, artifacts: list[Artifact]) -> None:
        self._artifact_ids = [artifact.id for artifact in artifacts]

    def add_artifact(self, artifact_id: str) -> None:
        if artifact_id not in self.artifact_ids:
            self.artifact_ids.append(artifact_id)