import networkx

from modstack.contracts.flows import FlowInput, FlowOutput, SocketId
from modstack.endpoints import Endpoint
from modstack.engines import EngineBase
from modstack.modules import Module

class Flow(EngineBase):
    @property
    def nodes(self) -> dict[str, Endpoint]:
        raise NotImplementedError()

    def __init__(self):
        self.graph = networkx.MultiDiGraph()

    def to_module(self) -> Module:
        pass

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

    def run(
        self,
        node_id: str | None = None,
        data: FlowInput | None = None,
        **kwargs
    ) -> FlowOutput:
        pass