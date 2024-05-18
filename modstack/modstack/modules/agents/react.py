from typing import Any, Iterable

from modstack.endpoints import endpoint
from modstack.modules.agents import Agent
from modstack.typing import ChatMessage

class ReactAgent(Agent):
    @endpoint
    def call(
        self,
        prompt: str,
        history: Iterable[ChatMessage] | None = None,
        generation_args: dict[str, Any] | None = None
    ) -> Iterable[ChatMessage]:
        pass