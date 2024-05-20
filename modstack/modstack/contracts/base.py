from abc import ABC
from typing import Generic, TypeVar

from modstack.typing import Serializable
from modstack.typing.vars import Out

class Contract(Serializable, Generic[Out], ABC):
    pass