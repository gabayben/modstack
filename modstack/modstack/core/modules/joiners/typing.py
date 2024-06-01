from modstack.core.typing import Artifact, Serializable, Variadic

class JoinArtifacts(Serializable):
    artifacts: Variadic[list[Artifact]]
    weights: list[float] | None = None
    top_k: int | None = None,
    sort_by_score: bool = True