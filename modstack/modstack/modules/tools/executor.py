from functools import partial
from typing import Any, Iterable, Sequence

from modstack.modules import SerializableModule
from modstack.modules.tools import Tool
from modstack.typing import Effect, Effects
from modstack.typing.messages import MessageArtifact

class ToolExecutor(SerializableModule[Iterable[MessageArtifact], Any]):
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

    def forward(self, data: Iterable[MessageArtifact], **kwargs) -> Effect[Any]:
        return Effects.Provide(
            invoke=partial(self._invoke, data, **kwargs),
            ainvoke=partial(self._ainvoke, data, **kwargs)
        )

    def _invoke(self, data: Iterable[MessageArtifact], **kwargs) -> Any:
        pass

    async def _ainvoke(self, data: Iterable[MessageArtifact], **kwargs) -> Any:
        pass