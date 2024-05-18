from typing import Any, Iterable

from modstack.contracts import Contract
from modstack.typing import ChatMessage, Tool

class CallLLM(Contract[Iterable[ChatMessage]]):
    prompt: str
    history: Iterable[ChatMessage] | None = None
    tools: list[Tool] | None = None
    generation_args: dict[str, Any] | None = None

    def __init__(
        self,
        prompt: str,
        history: Iterable[ChatMessage] | None = None,
        tools: list[Tool] | None = None,
        generation_args: dict[str, Any] | None = None,
        **kwargs
    ):
        super().__init__(
            prompt=prompt,
            history=history,
            tools=tools,
            generation_args=generation_args,
            **kwargs
        )

    @classmethod
    def name(cls) -> str:
        return 'call_llm'