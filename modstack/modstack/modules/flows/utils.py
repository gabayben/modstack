"""
Much of this code was taken from Haystack - https://github.com/deepset-ai/haystack/blob/main/haystack/core/pipeline/descriptions.py
SPDX-FileCopyrightText: 2022-present deepset GmbH <info@deepset.ai>
SPDX-License-Identifier: Apache-2.0
"""

from typing import Any, Union, get_args, get_origin

import networkx as nx
from pydantic.fields import FieldInfo

from modstack.constants import VARIADIC_TYPE
from modstack.modules.flows import FlowSockets, FlowSocketDescriptions, NodeSocket, NodeSocketDescription

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
        connections=[],
        required=info.is_required(),
        is_variadic=is_variadic
    )

def parse_connect_string(connection: str) -> tuple[str, str | None]:
    if '.' in connection:
        split_str = connection.split('.', maxsplit=1)
        return split_str[0], split_str[1]
    return connection, None

def types_are_compatible(source, target) -> bool:
    if source == target or target is Any:
        return True
    if source is Any:
        return False

    try:
        if issubclass(source, target):
            return True
    except TypeError:
        pass

    source_origin = get_origin(source)
    target_origin = get_origin(target)

    if source_origin is not Union and target_origin is Union:
        return any(types_are_compatible(source, union_arg) for union_arg in get_args(target))

    if not source_origin or not target_origin or source_origin != target_origin:
        return False

    source_args = get_args(source)
    target_args = get_args(target)
    if len(source_args) > len(target_args):
        return False

    return all(types_are_compatible(*args) for args in zip(source_args, target_args))

def find_flow_inputs(graph: nx.MultiDiGraph, include_connected: bool = False) -> FlowSockets:
    return {
        node: [
            socket
            for socket in data.get('input_sockets', {}).values()
            if socket.is_variadic or (include_connected or not socket.connections)
        ]
        for node, data in graph.nodes(data=True)
    }

def find_flow_outputs(graph: nx.MultiDiGraph, include_connected: bool = False) -> FlowSockets:
    return {
        node: [
            socket
            for socket in data.get('output_sockets', {}).values()
            if include_connected or not socket.connections
        ]
        for node, data in graph.nodes(data=True)
    }

def describe_flow_inputs(graph: nx.MultiDiGraph) -> FlowSocketDescriptions:
    return {
        node: {
            socket.name: NodeSocketDescription(annotation=socket.annotation, required=socket.required)
            for socket in sockets
        }
        for node, sockets in find_flow_inputs(graph).items()
        if sockets
    }

def describe_flow_inputs_as_string(graph: nx.MultiDiGraph) -> str:
    inputs = describe_flow_inputs(graph)
    message = 'This flow expects the following inputs:\n'
    for node, sockets in inputs.items():
        if sockets:
            message += f'- {node}:\n'
            for name, socket in sockets.items():
                message += f'    - {name}: {socket['annotation']}\n'
    return message