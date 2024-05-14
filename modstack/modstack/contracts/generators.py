from typing import Any, Iterator

from modstack.contracts import Contract
from modstack.typing import Utf8Artifact
from modstack.typing import ChatMessage

class GenerateText(Contract[list[Utf8Artifact]]):
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

class GenerateChat(Contract[Iterator[ChatMessage]]):
    messages: list[ChatMessage]
    generation_args: dict[str, Any] | None = None

    @classmethod
    def name(cls) -> str:
        return 'generate_chat'