from typing import Any

from modstack.modules import Module, ModuleLike
from modstack.typing import Effect
from modstack.typing.vars import In, Out

class Sequential(Module[In, Out]):
    def __init__(
        self,
        *args: ModuleLike,
        first: ModuleLike[In, Any] | None = None,
        middle: list[ModuleLike] | None = None,
        last: ModuleLike[Any, Out] | None = None,
        name: str | None = None
    ):
        pass

    def forward(self, data: In, **kwargs) -> Effect[Out]:
        pass