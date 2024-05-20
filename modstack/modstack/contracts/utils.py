from typing import Any

from modstack.contracts import Contract

class ToTextArtifacts(Contract):
    content: list[str]
    metadata: list[dict[str, Any]] | None = None