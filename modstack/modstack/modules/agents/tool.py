from typing import Any, Type, override

from pydantic import BaseModel

from modstack.contracts import ToolDef
from modstack.modules import Module, ModuleLike, coerce_to_module
from modstack.typing import Effect

class Tool(Module[dict[str, Any], Any]):
    function: Module
    metadata: dict[str, Any]

    def __init__(
        self,
        function: ModuleLike,
        name: str | None = None,
        description: str | None = None,
        args_schema: Type[BaseModel] | None = None,
        result_schema: Type[BaseModel] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.function = coerce_to_module(function)
        self.name = name or self.function.get_name()
        self.description = description or self.function.get_description()
        self._args_schema = args_schema or self.function.input_schema()
        self._result_schema = result_schema or self.function.output_schema()
        self.metadata = metadata or {}

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
        return self._args_schema

    @override
    def output_schema(self) -> Type[BaseModel]:
        return self._result_schema

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.get_name(),
            description=self.get_description(),
            args_schema=self.input_schema(),
            result_schema=self.output_schema(),
            metadata=self.metadata
        )