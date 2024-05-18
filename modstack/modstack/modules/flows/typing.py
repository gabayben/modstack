from typing import Type

from pydantic.fields import FieldInfo

from modstack.endpoints import Endpoint

def FlowNode(TypedDict):
    instance: Endpoint
    visits: int

def FlowEdge(TypedDict):
    key: str
    source: str
    source_field: str
    source_field_info: FieldInfo
    target: str
    target_field: str
    target_field_info: FieldInfo
    connection_type: Type