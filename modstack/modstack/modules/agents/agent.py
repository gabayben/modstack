from abc import ABC, abstractmethod
from typing import Any, Iterable

from modstack.modules import Module
from modstack.typing import ChatMessage, Tool

class Agent(Module, ABC):
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

    def __engine_init__(self) -> None:
        if self._initial_tools:
            self.add_tools(*self._initial_tools)

    def add_tools(self, *tools: str | Tool) -> None:
        self.validate_context()

    @abstractmethod
    def call(
        self,
        prompt: str,
        history: Iterable[ChatMessage] | None = None,
        generation_args: dict[str, Any] | None = None
    ) -> Iterable[ChatMessage]:
        pass