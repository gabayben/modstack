from typing import Any, Optional

from modstack.modules import ModuleLike, SerializableModule, coerce_to_module
from modstack.typing import Effect

class ToolExecutor(SerializableModule):
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