from typing import Optional

from modstack.artifacts import Artifact
from modstack.typing import Serializable

class RankArtifacts(Serializable):
    artifacts: list[Artifact]
    top_k: Optional[int] = None

    def __init__(
        self,
        artifacts: list[Artifact],
        top_k: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            artifacts=artifacts,
            top_k=top_k,
            **kwargs
        )

class RankLostInTheMiddle(RankArtifacts):
    word_count_threshold: Optional[int] = None