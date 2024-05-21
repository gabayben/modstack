from modstack.typing import Artifact, Serializable

class RankArtifacts(Serializable):
    artifacts: list[Artifact]

class RankLostInTheMiddle(RankArtifacts):
    top_k: int | None = None
    word_count_threshold: int | None = None