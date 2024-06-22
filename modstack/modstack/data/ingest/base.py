from abc import ABC, abstractmethod

class IngestDocument(ABC):
    pass

class IngestConnector(ABC):
    @abstractmethod
    def load(self, **kwargs) -> list[IngestDocument]:
        pass