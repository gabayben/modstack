from typing import Any

from modstack.commands import Command
from modstack.typing import TextArtifact

class ToTextArtifacts(Command[list[TextArtifact]]):
    content: list[str]
    metadata: list[dict[str, Any]] | None = None

    @classmethod
    def name(cls) -> str:
        return 'to_text_artifacts'