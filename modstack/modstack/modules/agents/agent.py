from abc import ABC, abstractmethod
from typing import Any, Iterable

from modstack.modules import Module
from modstack.typing import ChatMessage, Tool

class Agent(Module, ABC):
    def __init__(
        self,
        llm_path: str,
        tools: list[Tool] | None = None
    ):
        super().__init__()
        self.llm_path = llm_path
        self._tools = tools or []

    def add_tools(self, *tools: str | Tool) -> None:
        pass

    @abstractmethod
    def call(
        self,
        prompt: str,
        history: Iterable[ChatMessage] | None = None,
        generation_args: dict[str, Any] | None = None
    ) -> Iterable[ChatMessage]:
        pass