from typing import Any

from modstack.core.modules import Module, SerializableModule
from modstack.core.typing import Effect
from modstack.core.typing.vars import In, Out

class Parallel(SerializableModule[dict[str, Any], dict[str, Any]]):
    modules: dict[str, Module]

    def forward(self, data: In, **kwargs) -> Effect[Out]:
        pass