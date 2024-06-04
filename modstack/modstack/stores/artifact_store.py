from abc import ABC, abstractmethod
from enum import StrEnum

from modstack.artifacts import Artifact

class DuplicatePolicy(StrEnum):
    NONE = 'none'
    SKIP = 'skip'
    OVERWRITE = 'overwrite'
    FAIL = 'fail'

class ArtifactStore(ABC):
    @abstractmethod
    def get_artifacts(self, **kwargs):
        pass

    @abstractmethod
    def count_artifacts(self, **kwargs):
        pass

    @abstractmethod
    def write_artifacts(
        self,
        artifacts: list[Artifact],
        policy: DuplicatePolicy = DuplicatePolicy.NONE,
        **kwargs
    ) -> int:
        pass

    @abstractmethod
    def delete_artifacts(self, artifact_ids: list[str], **kwargs) -> None:
        pass