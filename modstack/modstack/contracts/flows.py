from typing import Any, NamedTuple

from modstack.contracts import Contract

class SocketId(NamedTuple):
    node: str
    field: str | None = None

FlowInput = dict[str, dict[str, Any]]
FlowOutput = dict[str, Any]

class RunFlow(Contract):
    node_id: str | None = None
    data: FlowInput | None = None

    def __init__(
        self,
        node_id: str | None = None,
        data: FlowInput | None = None,
        **kwargs
    ):
        super().__init__(node_id=node_id, data=data, **kwargs)