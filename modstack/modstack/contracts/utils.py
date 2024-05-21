from typing import Any, NamedTuple

class ToTextArtifacts(NamedTuple):
    content: list[str]
    metadata: list[dict[str, Any]] | dict[str, Any] | None = None