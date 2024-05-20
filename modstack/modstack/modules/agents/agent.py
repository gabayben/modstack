from abc import ABC, abstractmethod
from typing import Iterable

from modstack.contracts.agents import CallAgent
from modstack.modules import Modules
from modstack.typing import ChatMessage, Tool

class Agent(Modules.Sync[CallAgent, Iterable[ChatMessage]], ABC):
    @property
    def tools(self) -> list[Tool]:
        return self._tools

    def __init__(
        self,
        llm_path: str,
        tools: list[str | Tool] | None = None
    ):
        super().__init__()
        self.llm_path = llm_path
        self._initial_tools = tools
        self._tools: list[Tool] = []

    def add_tools(self, *tools: str | Tool) -> None:
        pass

    @abstractmethod
    def _invoke(self, data: CallAgent) -> Iterable[ChatMessage]:
        pass