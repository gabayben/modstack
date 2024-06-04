from typing import Any, NotRequired, TypedDict, Union

from pydantic import Field

from modstack.modules import Module
from modstack.typing import Serializable

FlowInput = dict[str, Union[Any, dict[str, Any]]]
FlowData = dict[str, dict[str, Any]]

class RunFlow(Serializable):
    data: FlowInput = Field(default_factory=dict)
    include_outputs_from: set[str] | None = None
    debug: bool = False

    def __init__(
        self,
        data: FlowInput = {},
        include_outputs_from: set[str] | None = None,
        debug: bool = False,
        **kwargs
    ):
        super().__init__(
            data=data,
            include_outputs_from=include_outputs_from,
            debug=debug,
            **kwargs
        )

class NodeSocket(Serializable):
    name: str
    description: str | None = None
    default: Any | None = None
    annotation: Any
    connections: list[str] = Field(default_factory=list)
    required: bool
    is_variadic: bool

class NodeSocketDescription(TypedDict):
    annotation: Any
    default: NotRequired[Any]
    required: NotRequired[bool]

FlowSockets = dict[str, list[NodeSocket]]
FlowSocketDescriptions = dict[str, dict[str, NodeSocketDescription]]

class FlowNode(TypedDict):
    name: str
    instance: Module
    input_sockets: dict[str, NodeSocket]
    output_sockets: dict[str, NodeSocket]
    is_greedy: bool
    visits: int

class FlowEdge(TypedDict):
    source_node: str
    target_node: str
    key: str
    conn_type: Any
    source_socket: NodeSocket
    target_socket: NodeSocket
    required: bool