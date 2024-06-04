from modstack.artifacts import Artifact
from modstack.typing import Serializable, Variadic

class JoinArtifacts(Serializable):
    artifacts: Variadic[list[Artifact]]
    weights: list[float] | None = None
    top_k: int | None = None,
    sort_by_score: bool = True