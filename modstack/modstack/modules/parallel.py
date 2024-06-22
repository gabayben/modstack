from typing import Any, Mapping, Optional, Type, Union, override

from pydantic import BaseModel

from modstack.modules import Module, ModuleLike, SerializableModule, coerce_to_module
from modstack.typing import Effect, Effects
from modstack.typing.vars import In

class Parallel(SerializableModule[In, dict[str, Any]]):
    modules: dict[str, Module]
    max_workers: Optional[int]

    @property
    @override
    def InputType(self) -> Type[In]:
        for module in self.modules.values():
            if module.InputType:
                return module.InputType
        return Any
    
    def __init__(
        self,
        steps: Mapping[
            str,
            Union[
                ModuleLike[In, Any],
                Mapping[str, ModuleLike[In, Any]]
            ]
        ],
        max_workers: Optional[int] = None
    ):
        super().__init__(
            modules={
                name: coerce_to_module(step)
                for name, step in steps.items()
            },
            max_workers=max_workers
        )

    def forward(self, data: dict[str, Any], **kwargs) -> Effect[dict[str, Any]]:
        return Effects.Parallel(
            {
                name: module.forward(data, **kwargs)
                for name, module in self.modules.items()
            },
            max_workers=self.max_workers
        )
    
    @override
    def get_name(
        self,
        name: str | None = None,
        suffix: str | None = None
    ) -> str:
        name = name or self.name or f'Parallel<{','.join(self.modules.keys())}>'
        return super().get_name(name=name, suffix=suffix)
    
    @override
    def input_schema(self) -> Type[BaseModel]:
        pass

    @override
    def output_schema(self) -> Type[BaseModel]:
        pass