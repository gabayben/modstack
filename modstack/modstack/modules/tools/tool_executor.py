from typing import Any, Optional

from modstack.modules import Module, ModuleLike, coerce_to_module
from modstack.typing import Effect

class ToolExecutor(Module):
    def __init__(
        self,
        tools: list[ModuleLike],
        name: str = 'tools',
        tags: Optional[list[str]] = None
    ):
        self.tools = [coerce_to_module(tool) for tool in tools]
        self.name = name
        self.tags = tags

    def forward(self, data: Any, **kwargs) -> Effect[Any]:
        pass