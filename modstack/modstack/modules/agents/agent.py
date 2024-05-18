from typing import Any, Dict, Iterable

from modstack.contracts import Tool
from modstack.endpoints import endpoint
from modstack.engines import Engine
from modstack.modules import Module
from modstack.typing import ChatMessage

class Agent(Module):
    def __init__(
        self,
        engine: Engine,
        llm_path: str,
        tools: list[Tool] | None = None
    ):
        self.llm_path = llm_path
        self._tools = tools or []

    def add_tools(self, *tools: Tool) -> None:
        pass

    @endpoint
    def call(
        self,
        messages: Iterable[ChatMessage],
        generation_args: Dict[str, Any]
    ) -> Iterable[ChatMessage]:
        pass