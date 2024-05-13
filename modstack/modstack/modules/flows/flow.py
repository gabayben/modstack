import networkx

from modstack.contracts.flows import FlowInput, FlowOutput, NodeId, RunFlow, SocketId
from modstack.containers import Feature, feature
from modstack.modules import Module

class Flow(Module):
    @property
    def nodes(self) -> dict[NodeId, Feature]:
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

    @feature(name=RunFlow.name())
    def run(
        self,
        node_id: NodeId | None = None,
        data: FlowInput | None = None,
        **kwargs
    ) -> FlowOutput:
        pass