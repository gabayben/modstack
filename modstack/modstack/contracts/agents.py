from typing import Any, Iterable

from modstack.typing import ChatMessage, Serializable

class AgentRequest(Serializable):
    prompt: str
    history: Iterable[ChatMessage] | None = None
    generation_args: dict[str, Any] | None = None

    def __init__(
        self,
        prompt: str,
        history: Iterable[ChatMessage] | None = None,
        generation_args: dict[str, Any] | None = None,
        **kwargs
    ):
        super().__init__(
            prompt=prompt,
            history=history,
            generation_args=generation_args,
            **kwargs
        )