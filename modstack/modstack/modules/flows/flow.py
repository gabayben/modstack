import networkx

from modstack.commands import CommandHandler, CommandId, command
from modstack.commands.flows import FlowInput, FlowOutput, RunFlow, SocketId
from modstack.modules import Module

class Flow(Module):
    def __init__(self):
        self.graph = networkx.MultiDiGraph()

    def add_node(
        self,
        node: CommandHandler | Module,
        name: str | None = None
    ) -> None:
        pass

    def connect(
        self,
        source: SocketId,
        target: SocketId
    ) -> None:
        pass

    @command(RunFlow)
    def run(
        self,
        node: CommandId | None = None,
        data: FlowInput | None = None,
        **kwargs
    ) -> FlowOutput:
        pass