from modstack.artifacts import Artifact
from modstack.typing import Schema

class CohereRankRequest(Schema):
    query: str
    artifacts: list[Artifact]