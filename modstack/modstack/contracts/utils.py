from typing import Any

from modstack.contracts import Contract
from modstack.typing import TextArtifact

class ToTextArtifacts(Contract[list[TextArtifact]]):
    content: list[str]
    metadata: list[dict[str, Any]] | None = None

    @classmethod
    def name(cls) -> str:
        return 'to_text_artifacts'