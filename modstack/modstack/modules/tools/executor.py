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
        def invoke() -> Any:
            return self._invoke(data, **kwargs)

        async def ainvoke() -> Any:
            return await self._ainvoke(data, **kwargs)

        return Effects.Provide(invoke=invoke, ainvoke=ainvoke)

    def _invoke(self, data: Iterable[MessageArtifact], **kwargs) -> Any:
        pass

    async def _ainvoke(self, data: Iterable[MessageArtifact], **kwargs) -> Any:
        pass