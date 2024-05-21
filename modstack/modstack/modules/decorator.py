from typing import Any

from modstack.modules import Module
from modstack.typing import Effect
from modstack.typing.vars import In, Out

class DecoratorBase(Module[In, Out]):
    bound: Module[In, Out]
    kwargs: dict[str, Any]

    def forward(self, data: In, **kwargs) -> Effect[Out]:
        return self.bound.forward(data, **self.kwargs, **kwargs)