import networkx

from modstack.commands import CommandHandler
from modstack.modules import Module
from modstack.modules.flows import NodeId, SocketId

class Flow(Module):
    @property
    def nodes(self) -> dict[NodeId, CommandHandler]:
        raise NotImplementedError()

    def __init__(self):
        self.graph = networkx.MultiDiGraph()

    def add_module(
        self,
        module: Module,
        name: str | None = None
    ) -> None:
        pass

    def connect(
        self,
        source: SocketId,
        target: SocketId
    ) -> None:
        pass