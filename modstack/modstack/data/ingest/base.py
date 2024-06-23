from abc import ABC, abstractmethod
from typing import Optional

from modstack.artifacts import Artifact
from modstack.artifacts.layout import ElementSourceMetadata

class IngestDocument(ABC):
    _source_metadata: Optional[ElementSourceMetadata] = None

    @property
    def source_metadata(self) -> ElementSourceMetadata:
        if not self._source_metadata:
            raise ValueError('Source metadata not set.')
        return self._source_metadata

    @source_metadata.setter
    def source_metadata(self, source_metadata: ElementSourceMetadata) -> None:
        self._source_metadata = source_metadata

    def update_source_metadata(self, **kwargs) -> None:
        pass

    @abstractmethod
    def load(self, **kwargs) -> None:
        pass

    @abstractmethod
    def get_artifact(self, **kwargs) -> Artifact:
        pass

class IngestConnector(ABC):
    @abstractmethod
    def connect(self, **kwargs) -> list[IngestDocument]:
        pass