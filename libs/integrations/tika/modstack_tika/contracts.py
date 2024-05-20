from typing import Any

from modstack.contracts import Contract
from modstack.typing import ArtifactSource

class TikaToText(Contract):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None