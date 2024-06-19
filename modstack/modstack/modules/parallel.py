from typing import Any

from modstack.modules import Module, SerializableModule
from modstack.typing import Effect

class Parallel(SerializableModule[dict[str, Any], dict[str, Any]]):
    modules: dict[str, Module]

    def forward(self, data: dict[str, Any], **kwargs) -> Effect[dict[str, Any]]:
        pass