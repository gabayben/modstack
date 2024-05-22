from typing import Any, Type, cast, override

from pydantic import BaseModel, Field

from modstack.modules import Module, ModuleLike, SerializableModule, coerce_to_module
from modstack.modules.base import ModuleMapping
from modstack.modules.traits import HasSequentialSchema
from modstack.typing import Effect
from modstack.typing.vars import In, Other, Out

def _seq_input_schema(steps: list[Module]) -> Type[BaseModel]:
    first = steps[0]
    if len(steps) == 1:
        return first.input_schema()
    elif isinstance(first, HasSequentialSchema):
        return first.seq_input_schema(_seq_input_schema(steps[1:]))
    return first.input_schema()

def _seq_output_schema(steps: list[Module]) -> Type[BaseModel]:
    last = steps[-1]
    if len(steps) == 1:
        return last.input_schema()
    elif isinstance(last, HasSequentialSchema):
        return last.seq_output_schema(_seq_output_schema(steps[:-1]))
    return last.output_schema()

class Sequential(SerializableModule[In, Out]):
    first: Module[In, Any]
    middle: list[Module] = Field(default_factory=list)
    last: Module[Any, Out]

    @property
    @override
    def InputType(self) -> Type[In]:
        return self.first.InputType

    @property
    @override
    def OutputType(self) -> Type[Out]:
        return self.last.OutputType

    @property
    def steps(self) -> list[Module]:
        return [self.first] + self.middle + [self.last]

    def __init__(
        self,
        *steps: Module,
        first: Module[In, Any] | None = None,
        middle: list[Module] | None = None,
        last: Module[Any, Out] | None = None,
        name: str | None = None
    ):
        steps_flat: list[Module] = []
        if not steps:
            if first is not None and last is not None:
                steps_flat = [first] + (middle or []) + [last]
        else:
            for step in steps:
                if isinstance(step, Sequential):
                    steps_flat.extend(step.steps)
                else:
                    steps_flat.append(step)
        if len(steps_flat) < 2:
            raise ValueError(f'Sequential must have at least 2 steps, got {len(steps_flat)}.')
        super().__init__(
            name=name,
            first=steps_flat[0],
            middle=list(steps_flat[1:-1]),
            last=steps_flat[-1]
        )

    def __or__(
        self,
        other: ModuleLike[Out, Other] | ModuleMapping[Out]
    ) -> Module[In, Other]:
        if isinstance(other, Sequential):
            return Sequential(
                self.first,
                *self.middle,
                self.last,
                other.first,
                *other.middle,
                other.last,
                name=self.name or other.name
            )
        return Sequential(
            self.first,
            *self.middle,
            self.last,
            coerce_to_module(other),
            name=self.name
        )

    def __ror__(self, other: ModuleLike[Other, In]) -> Module[Other, Out]:
        if isinstance(other, Sequential):
            return Sequential(
                other.first,
                *other.middle,
                other.last,
                self.first,
                *self.middle,
                self.last,
                name=other.name or self.name
            )
        return Sequential(
            coerce_to_module(other),
            self.first,
            *self.middle,
            self.last,
            name=self.name
        )

    def forward(self, data: In, **kwargs) -> Effect[Out]:
        try:
            effect = self.steps[0].forward(data, **kwargs)
            for step in self.steps[1:]:
                effect = effect.flat_map(lambda out: step.forward(out, **kwargs))
        except:
            raise
        else:
            return cast(Effect[Out], effect)

    def input_schema(self) -> Type[BaseModel]:
        return _seq_input_schema(self.steps)

    def output_schema(self) -> Type[BaseModel]:
        return _seq_output_schema(self.steps)