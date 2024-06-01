from typing import Any

from modstack.core.typing import ArtifactSource, Serializable

class ToText(Serializable):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None