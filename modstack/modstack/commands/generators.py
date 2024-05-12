from typing import Any

from pydantic import Field

from modstack.commands import Command
from modstack.typing import Serializable

class TextGeneration(Serializable):
    results: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)

class GenerateText(Command[TextGeneration]):
    prompt: str
    generation_args: dict[str, Any] | None = None