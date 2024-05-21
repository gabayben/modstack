from abc import ABC, abstractmethod
from typing import Any, Iterable

from modstack.contracts import AgenticLLMRequest
from modstack.contracts.agents import AgentRequest
from modstack.modules import Module
from modstack.tools import Tool
from modstack.typing import ChatMessage, Effect
from modstack.typing.vars import In, Out

class Agent(Module[AgentRequest, Iterable[ChatMessage]], ABC):
    @property
    def tools(self) -> dict[str, Tool]:
        return self._tools

    def __init__(
        self,
        llm: Module[AgenticLLMRequest, Iterable[ChatMessage]],
        tools: list[Tool] | None = None
    ):
        super().__init__()
        self.llm = llm
        self._tools: dict[str, Tool] = {}
        if tools:
            self.add_tools(*tools)

    def add_tools(self, *tools: Tool) -> None:
        for tool in tools:
            self.tools[tool.name] = tool

    def forward(self, data: In, **kwargs) -> Effect[Out]:
        pass

    @abstractmethod
    def _step(self, data: Any, **kwargs) -> Any:
        pass