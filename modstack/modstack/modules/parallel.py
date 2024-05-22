from typing import Any

from modstack.modules import Module, SerializableModule
from modstack.typing import Effect
from modstack.typing.vars import In, Out

class Parallel(SerializableModule[dict[str, Any], dict[str, Any]]):
    modules: dict[str, Module]

    def forward(self, data: In, **kwargs) -> Effect[Out]:
        pass