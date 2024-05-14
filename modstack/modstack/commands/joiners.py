from abc import ABC

from modstack.commands import Command
from modstack.typing import Artifact, Variadic

class JoinArtifacts(Command[list[Artifact]], ABC):
    artifacts: Variadic[list[Artifact]]
    weights: list[float] | None = None
    top_k: int | None = None,
    sort_by_score: bool = True

class ConcatArtifacts(JoinArtifacts):
    @classmethod
    def name(cls) -> str:
        return 'concat_artifacts'

class MergeArtifacts(JoinArtifacts):
    @classmethod
    def name(cls) -> str:
        return 'merge_artifacts'

class ReciprocalRankFusion(JoinArtifacts):
    @classmethod
    def name(cls) -> str:
        return 'reciprocal_rank_fusion'