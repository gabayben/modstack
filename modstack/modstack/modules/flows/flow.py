import networkx

from modstack.commands import CommandHandler, command
from modstack.commands.flows import FlowInput, FlowOutput, NodeId, RunFlow, SocketId
from modstack.modules import Module

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

    @command(RunFlow, name='run_flow')
    def run(
        self,
        node_id: NodeId | None = None,
        data: FlowInput | None = None,
        **kwargs
    ) -> FlowOutput:
        pass