from typing import Any, Iterable, Sequence

from modstack.modules import Module
from modstack.modules.tools import Tool
from modstack.typing import ChatMessage, Effect

class ToolExecutor(Module[Iterable[ChatMessage], Any]):
    @property
    def tools(self) -> dict[str, Tool]:
        return self._tools

    def __init__(self, tools: Sequence[Tool]):
        super().__init__()
        self._tools: dict[str, Tool] = {}
        self.add_tools(*tools)

    def add_tools(self, *tools: Tool) -> None:
        for tool in tools:
            self.tools[tool.name] = tool

    def forward(self, data: Iterable[ChatMessage], **kwargs) -> Effect[Any]:
        pass