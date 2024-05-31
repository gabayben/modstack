from typing import get_args

from pydantic.fields import FieldInfo

from modstack.constants import VARIADIC_TYPE
from modstack.modules.flows import NodeSocket

def create_node_socket(name: str, info: FieldInfo) -> NodeSocket:
    try:
        is_variadic = info.metadata[0] == VARIADIC_TYPE
    except (AttributeError, IndexError):
        is_variadic = False
    annotation = get_args(info.annotation)[0] if is_variadic else info.annotation
    return NodeSocket(
        name=name,
        description=info.description,
        default=info.default,
        annotation=annotation,
        connected_to=[],
        required=info.is_required(),
        is_variadic=is_variadic
    )

def parse_connect_string(connection: str) -> tuple[str, str | None]:
    if '.' in connection:
        split_str = connection.split('.', maxsplit=1)
        return split_str[0], split_str[1]
    return connection, None

def types_are_compatible(source, target) -> bool:
    pass