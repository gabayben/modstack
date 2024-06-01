from typing import Any

from modstack.core.artifacts import ArtifactSource
from modstack.core.typing import Serializable

class ToText(Serializable):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None