from typing import Any, NamedTuple, Type

from modstack.commands import Command

class NodeId(NamedTuple):
    command: Type[Command]
    module: str | None = None

class SocketId(NodeId):
    field: str | None = None

FlowInput = dict[NodeId, dict[str, Any]]
FlowOutput = dict[NodeId, Any]

class RunFlow(Command[FlowOutput]):
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