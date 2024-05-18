from typing import Any, Dict, Iterable

from modstack.endpoints import endpoint
from modstack.engines import EngineContext
from modstack.modules import Module
from modstack.typing import ChatMessage, Tool

class Agent(Module):
    def __init__(
        self,
        context: EngineContext,
        llm_path: str,
        tools: list[Tool] | None = None
    ):
        self.context = context
        self.llm_path = llm_path
        self._tools = tools or []

    def add_tools(self, *tools: str | Tool) -> None:
        pass

    @endpoint
    def call(
        self,
        messages: Iterable[ChatMessage],
        generation_args: Dict[str, Any]
    ) -> Iterable[ChatMessage]:
        pass