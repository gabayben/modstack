from typing import Any, Iterable

from modstack.contracts import Contract
from modstack.typing import ChatMessage

class CallAgent(Contract[Iterable[ChatMessage]]):
    prompt: str
    history: Iterable[ChatMessage] | None = None
    generation_args: dict[str, Any] | None = None

    def __init__(
        self,
        prompt: str,
        history: Iterable[ChatMessage] | None = None,
        generation_args: dict[str, Any] | None = None
    ):
        super().__init__(
            prompt=prompt,
            history=history,
            generation_args=generation_args
        )