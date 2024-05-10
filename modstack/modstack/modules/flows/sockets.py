from typing import Any, Generic, NamedTuple, Type

from modstack.core import Command
from modstack.typing.vars import Out

class NodeId(NamedTuple, Generic[Out]):
    name: str
    command: Type[Command[Out]]

class SocketId(NodeId[Any]):
    field: str | None = None