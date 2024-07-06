from pydantic import PrivateAttr

from modstack.query.structs import IndexStruct

class GraphStruct(IndexStruct):
    _artifact_ids: set[str] = PrivateAttr(default_factory=set)

    @property
    def artifact_ids(self) -> list[str]:
        return list(self._artifact_ids)

    @artifact_ids.setter
    def artifact_ids(self, artifact_ids: set[str]) -> None:
        self._artifact_ids = artifact_ids

    def add_artifact(self, artifact_id: str) -> None:
        self._artifact_ids.add(artifact_id)

    def delete_artifact(self, artifact_id: str) -> None:
        self._artifact_ids.remove(artifact_id)