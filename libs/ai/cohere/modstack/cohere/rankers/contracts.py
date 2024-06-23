from modstack.artifacts import Utf8Artifact
from modstack.typing import Schema

class CohereRankRequest(Schema):
    query: str
    artifacts: list[Utf8Artifact]