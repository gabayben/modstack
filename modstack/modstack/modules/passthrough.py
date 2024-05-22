from modstack.modules import SerializableModule
from modstack.typing import Effect
from modstack.typing.vars import In, Out

class Passthrough(SerializableModule[In, Out]):
    def forward(self, data: In, **kwargs) -> Effect[Out]:
        pass