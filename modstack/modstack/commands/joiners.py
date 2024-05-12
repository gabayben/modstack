from modstack.commands import Command
from modstack.typing import Artifact, Variadic

class JoinArtifacts(Command[list[Artifact]]):
    artifacts: Variadic[list[Artifact]]
    weights: list[float] | None = None
    top_k: int | None = None,
    sort_by_score: bool = True