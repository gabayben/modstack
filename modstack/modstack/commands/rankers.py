from typing import override

from modstack.commands import Command
from modstack.typing import Artifact

class RankArtifacts(Command[list[Artifact]]):
    artifacts: list[Artifact]

    @classmethod
    def name(cls) -> str:
        return 'rank_artifacts'

class RankLostInTheMiddle(RankArtifacts):
    top_k: int | None = None
    word_count_threshold: int | None = None

    @classmethod
    @override
    def name(cls) -> str:
        return 'rank_lost_in_the_middle'