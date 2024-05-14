from typing import Any, Iterator

from modstack.contracts import Contract
from modstack.typing import ChatMessage

class LLMCall(Contract[Iterator[ChatMessage]]):
    messages: list[ChatMessage]
    generation_args: dict[str, Any] | None = None

    @classmethod
    def name(cls) -> str:
        return 'generate_chat'