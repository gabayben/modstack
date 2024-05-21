from typing import Any, Type, cast, override

from pydantic import BaseModel

from modstack.modules import Module
from modstack.typing import Effect
from modstack.typing.vars import In, Out

class DecoratorBase(Module[In, Out]):
    bound: Module[In, Out]
    kwargs: dict[str, Any]
    custom_input_type: Type[In] | BaseModel | None
    custom_output_type: Type[Out] | BaseModel | None

    @property
    @override
    def InputType(self) -> Type[In]:
        return (
            cast(Type[In], self.custom_input_type)
            if self.custom_input_type is not None
            else self.bound.InputType
        )

    @property
    @override
    def OutputType(self) -> Type[Out]:
        return (
            cast(Type[Out], self.custom_output_type)
            if self.custom_output_type is not None
            else self.bound.OutputType
        )

    def __init__(
        self,
        bound: Module[In, Out],
        kwargs: dict[str, Any] | None = None,
        custom_input_type: Type[In] | BaseModel | None = None,
        custom_output_type: Type[Out] | BaseModel | None = None,
        **fields
    ):
        super().__init__(
            bound=bound,
            kwargs=kwargs or {},
            custom_input_type=custom_input_type,
            custom_output_type=custom_output_type,
            **fields
        )

    def forward(self, data: In, **kwargs) -> Effect[Out]:
        return self.bound.forward(data, **self.kwargs, **kwargs)

    @override
    def get_name(
        self,
        name: str | None = None,
        suffix: str | None = None
    ) -> str:
        return self.bound.get_name(name=name, suffix=suffix)

    @override
    def input_schema(self) -> Type[BaseModel]:
        if self.custom_input_type is not None:
            return super().input_schema()
        return self.bound.input_schema()

    @override
    def output_schema(self) -> Type[BaseModel]:
        if self.custom_output_type is not None:
            return super().output_schema()
        return self.bound.output_schema()

class Decorator(DecoratorBase[In, Out]):
    @override
    def bind(self, **kwargs) -> 'Module[In, Out]':
        return self.__class__(
            bound=self.bound,
            kwargs={**self.kwargs, **kwargs},
            custom_input_type=self.custom_input_type,
            custom_output_type=self.custom_output_type
        )

    @override
    def with_types(
        self,
        custom_input_type: Type[In] | BaseModel | None = None,
        custom_output_type: Type[Out] | BaseModel | None = None
    ) -> 'Module[In, Out]':
        return self.__class__(
            bound=self.bound,
            kwargs=self.kwargs,
            custom_input_type=custom_input_type or self.custom_input_type,
            custom_output_type=custom_output_type or self.custom_output_type
        )

    @override
    def with_retry(self, **kwargs) -> 'Module[In, Out]':
        return self.__class__(
            bound=self.bound.with_retry(**kwargs),
            kwargs=self.kwargs,
            custom_input_type=self.custom_input_type,
            custom_output_type=self.custom_output_type
        )

    @override
    def with_fallbacks(self, **kwargs) -> 'Module[In, Out]':
        return self.__class__(
            bound=self.bound.with_fallbacks(**kwargs),
            kwargs=self.kwargs,
            custom_input_type=self.custom_input_type,
            custom_output_type=self.custom_output_type
        )