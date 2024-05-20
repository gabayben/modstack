from modstack.contracts import Contract
from modstack.typing import Artifact

class RankArtifacts(Contract):
    artifacts: list[Artifact]

class RankLostInTheMiddle(RankArtifacts):
    top_k: int | None = None
    word_count_threshold: int | None = None