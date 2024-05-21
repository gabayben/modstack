from typing import Any

from modstack.modules import Module, ModuleLike, coerce_to_module
from modstack.tools import ToolParameter
from modstack.typing import Effect

class Tool(Module[dict[str, Any], Any]):
    function: Module
    description: str
    parameters: dict[str, ToolParameter]
    metadata: dict[str, Any]

    def __init__(
        self,
        function: ModuleLike,
        name: str | None = None,
        description: str | None = None,
        parameters: dict[str, ToolParameter] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.function = coerce_to_module(function)
        self.name = name or self.function.get_name()
        self.description = description or self._default_description()
        self.parameters = parameters or self._default_parameters()
        self.metadata = metadata or {}

    def _default_description(self) -> str:
        pass

    def _default_parameters(self) -> dict[str, ToolParameter]:
        pass

    def forward(self, data: dict[str, Any], **kwargs) -> Effect[Any]:
        pass