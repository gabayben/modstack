from typing import Any, NamedTuple, Type

from modstack.commands import Command

class NodeId(NamedTuple):
    name: str
    command: Type[Command[Any]]

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