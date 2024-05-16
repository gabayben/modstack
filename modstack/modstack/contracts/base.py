from abc import ABC
from typing import Generic

from modstack.typing import Serializable
from modstack.typing.vars import Out

class Contract(Serializable, Generic[Out], ABC):
    @classmethod
    def name(cls) -> str:
        return cls.__name__