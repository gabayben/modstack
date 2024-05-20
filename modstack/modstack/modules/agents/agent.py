from abc import ABC

from modstack.typing import Tool

class Agent(ABC):
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