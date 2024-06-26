from typing import Any, Type, final, override

from pydantic import BaseModel

from modstack.core import Module, ModuleLike, SerializableModule, coerce_to_module
from modstack.typing import Effect

@final
class ToolWrapper(SerializableModule[dict[str, Any], Any]):
    function: Module

    def __init__(
        self,
        function: ModuleLike,
        name: str | None = None,
        description: str | None = None,
        input_schema: Type[BaseModel] | None = None,
        output_schema: Type[BaseModel] | None = None
    ):
        super().__init__()
        self.function = coerce_to_module(function)
        self.name = name or self.function.get_name()
        self.description = description or self.function.get_description()
        self._input_schema = input_schema or self.function.input_schema()
        self._output_schema = output_schema or self.function.output_schema()

    def forward(self, data: dict[str, Any], **kwargs) -> Effect[Any]:
        return self.function.forward(self.function.construct_input(data), **kwargs)

    @override
    def get_name(
        self,
        name: str | None = None,
        suffix: str | None = None
    ) -> str:
        return self.name

    @override
    def get_description(self, description: str | None = None) -> str:
        return self.description

    @override
    def input_schema(self) -> Type[BaseModel]:
        return self._input_schema

    @override
    def output_schema(self) -> Type[BaseModel]:
        return self._output_schema