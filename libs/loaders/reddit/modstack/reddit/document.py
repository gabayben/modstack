from modstack.artifacts import Artifact
from modstack.ingest import IngestDocument

class RedditDocument(IngestDocument):
    def load(self, **kwargs) -> None:
        pass

    def get_artifact(self, **kwargs) -> Artifact:
        pass