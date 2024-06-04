from typing import Any

from modstack.artifacts import ArtifactSource
from modstack.typing import Serializable

class ToText(Serializable):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None