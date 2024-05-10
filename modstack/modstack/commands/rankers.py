from modstack.core import Command
from modstack.typing import Artifact

class RankArtifacts(Command[list[Artifact]]):
    artifacts: list[Artifact]

class RankLostInTheMiddle(RankArtifacts):
    top_k: int | None = None
    word_count_threshold: int | None = None