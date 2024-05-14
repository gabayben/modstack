from typing import Any, NamedTuple

from modstack.contracts import Contract

class NodeId(NamedTuple):
    feature_name: str
    module_name: str | None = None

class SocketId(NodeId):
    field: str | None = None

FlowInput = dict[NodeId, dict[str, Any]]
FlowOutput = dict[NodeId, Any]

class RunFlow(Contract[FlowOutput]):
    node_id: NodeId | None = None
    data: FlowInput | None = None

    def __init__(
        self,
        node_id: NodeId | None = None,
        data: FlowInput | None = None,
        **kwargs
    ):
        super().__init__(node_id=node_id, data=data, **kwargs)

    @classmethod
    def name(cls) -> str:
        return 'run_flow'