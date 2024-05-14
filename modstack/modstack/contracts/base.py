from abc import ABC, abstractmethod
from typing import Generic

from modstack.typing import Serializable
from modstack.typing.vars import Out

class Contract(Serializable, Generic[Out], ABC):
    @classmethod
    @abstractmethod
    def name(cls) -> str:
        pass