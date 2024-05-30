from typing import TypedDict

from pydantic.fields import FieldInfo

from modstack.modules import Module

class FlowNode(TypedDict):
    name: str
    instance: Module
    input_sockets: dict[str, FieldInfo]
    output_sockets: dict[str, FieldInfo]
    visits: int