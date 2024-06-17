from functools import partial
import inspect
from typing import Type, final, override

from pydantic import BaseModel

from modstack.modules import Module, ModuleFunction
from modstack.typing import Effect, Effects
from modstack.typing.vars import In, Out
from modstack.utils.reflection import get_callable_type

class Functional(Module[In, Out]):
    @property
    @override
    @final
    def InputType(self) -> Type[In]:
        return self.parameter.annotation or super().InputType

    @property
    @override
    @final
    def OutputType(self) -> Type[Out]:
        return self.signature.return_annotation or super().OutputType

    def __init__(
        self,
        func: ModuleFunction[In, Out],
        name: str | None = None,
        description: str | None = None,
        input_schema: Type[BaseModel] | None = None,
        output_schema: Type[BaseModel] | None = None
    ):
        self.callable_type = get_callable_type(func)

        self.signature = inspect.signature(func)
        parameters = {key: value for key, value in self.signature.parameters.items() if value.annotation != inspect.Parameter.empty}
        if len(parameters) == 0:
            raise ValueError('A function that is decorated with `@module` must have an input.')
        self.parameter = list(parameters.values())[0]

        self._func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__
        self._input_schema = input_schema
        self._output_schema = output_schema

    @final
    def forward(self, data: In, **kwargs) -> Effect[Out]:
        if self.callable_type == 'effect':
            return self._func(data, **kwargs)
        func = partial(self._func, data, **kwargs)
        if self.callable_type == 'aiter':
            return Effects.AsyncIterator(func)
        elif self.callable_type == 'iter':
            return Effects.Iterator(func)
        elif self.callable_type == 'ainvoke':
            return Effects.Async(func)
        return Effects.Sync(func)

    @override
    def get_name(
        self,
        name: str | None = None,
        suffix: str | None = None
    ) -> str:
        return super().get_name(name=self.name, suffix=suffix)

    @override
    def get_description(self, description: str | None = None) -> str:
        return super().get_description(description=self.description)

    @override
    def input_schema(self) -> Type[BaseModel]:
        return self._input_schema or super().input_schema()

    @override
    def output_schema(self) -> Type[BaseModel]:
        return self._output_schema or super().output_schema()