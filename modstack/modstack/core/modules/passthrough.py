from modstack.core.modules import SerializableModule
from modstack.core.typing import Effect, Effects
from modstack.core.typing.vars import Other

class Passthrough(SerializableModule[Other, Other]):
    def forward(self, data: Other, **kwargs) -> Effect[Other]:
        return Effects.Value(data)