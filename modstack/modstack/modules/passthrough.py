from modstack.modules import SerializableModule
from modstack.typing import Effect, Effects
from modstack.typing.vars import Other

class Passthrough(SerializableModule[Other, Other]):
    def forward(self, data: Other, **kwargs) -> Effect[Other]:
        return Effects.Value(data)