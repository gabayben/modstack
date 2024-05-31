from typing import Any, TypedDict

from modstack.modules import Module
from modstack.typing import Serializable

class NodeSocket(Serializable):
    name: str
    description: str | None
    default: Any | None
    annotation: Any
    connected_to: list[str]
    required: bool
    is_variadic: bool

class FlowNode(TypedDict):
    name: str
    instance: Module
    input_sockets: dict[str, NodeSocket]
    output_sockets: dict[str, NodeSocket]
    visits: int

class FlowEdge(TypedDict):
    source_node: str
    target_node: str
    key: str
    conn_type: Any
    source_socket: NodeSocket
    target_socket: NodeSocket
    required: bool