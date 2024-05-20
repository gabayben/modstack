from modstack.contracts import Contract
from modstack.typing import Artifact, Variadic

class JoinArtifacts(Contract):
    artifacts: Variadic[list[Artifact]]
    weights: list[float] | None = None
    top_k: int | None = None,
    sort_by_score: bool = True