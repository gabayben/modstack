from modstack.core.artifacts import Artifact
from modstack.core.typing import Serializable

class RankArtifacts(Serializable):
    artifacts: list[Artifact]

class RankLostInTheMiddle(RankArtifacts):
    top_k: int | None = None
    word_count_threshold: int | None = None