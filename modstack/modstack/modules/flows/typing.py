from typing import NamedTuple, Type, TypedDict

from pydantic.fields import FieldInfo

from modstack.endpoints import Endpoint

class FlowSocket(NamedTuple):
    name: str
    field: FieldInfo
    connections: list[str]

class FlowNode(TypedDict):
    name: str
    instance: Endpoint
    input_sockets: dict[str, FlowSocket]
    output_sockets: dict[str, FlowSocket]
    visits: int

class FlowEdge(TypedDict):
    key: str
    source: str
    source_socket: FlowSocket
    target: str
    target_socket: FlowSocket
    connection_type: Type