from typing import Any

from pydantic import Field

from modstack.contracts import Contract
from modstack.typing import Serializable

class TextGeneration(Serializable):
    results: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)

class GenerateText(Contract[TextGeneration]):
    prompt: str
    generation_args: dict[str, Any] | None = None

    @classmethod
    def name(cls) -> str:
        return 'generate_text'