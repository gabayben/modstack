from abc import ABC, abstractmethod
from typing import Optional

from modstack.artifacts import Artifact
from modstack.artifacts.layout import ElementSourceMetadata
from modstack.utils.threading import run_async

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

    async def aload(self, **kwargs) -> None:
        await run_async(self.load, **kwargs)

    @abstractmethod
    def get_artifact(self, **kwargs) -> Artifact:
        pass

    async def aget_artifact(self, **kwargs) -> Artifact:
        return await run_async(self.get_artifact, **kwargs)