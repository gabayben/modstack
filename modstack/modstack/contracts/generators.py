from typing import Any

from pydantic import Field

from modstack.contracts import Contract
from modstack.typing import Serializable

class TextGeneration(Serializable):
    results: list[str]
    metadata: list[dict[str, Any]] = Field(default_factory=list)

    def __init__(
        self,
        results: list[str],
        metadata: list[dict[str, Any]] = []
    ):
        super().__init__(results=results, metadata=metadata)

class GenerateText(Contract[TextGeneration]):
    prompt: str
    generation_args: dict[str, Any] | None = None

    def __init__(
        self,
        prompt: str,
        generation_args: dict[str, Any] | None = None,
        **kwargs
    ):
        super().__init__(prompt=prompt, generation_args=generation_args, **kwargs)

    @classmethod
    def name(cls) -> str:
        return 'generate_text'