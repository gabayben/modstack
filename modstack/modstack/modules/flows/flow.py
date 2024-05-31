"""
Much of this code was taken from Haystack - https://github.com/deepset-ai/haystack/blob/main/haystack/core/pipeline/base.py
SPDX-FileCopyrightText: 2022-present deepset GmbH <info@deepset.ai>
SPDX-License-Identifier: Apache-2.0
"""

from functools import partial
import logging

import networkx as nx
from pydantic.fields import FieldInfo

from modstack.constants import DEBUG
from modstack.contracts.flows import FlowOutput, RunFlow
from modstack.exceptions import FlowConnectError
from modstack.modules import ModuleLike, SerializableModule, coerce_to_module
from modstack.modules.flows import NodeSocket
from modstack.modules.flows.typing import FlowNode
from modstack.modules.flows.utils import create_node_socket, parse_connect_string, types_are_compatible
from modstack.typing import Effect, Effects
from modstack.utils.func import tproduct

logger = logging.getLogger(__name__)

class Flow(SerializableModule[RunFlow, FlowOutput]):
    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def add_node(self, name: str, node: ModuleLike) -> None:
        if self.graph.has_node(name):
            raise ValueError(f"A node named '{name}' already exists in this flow: choose another name.")
        if name == DEBUG:
            raise ValueError(f"'{DEBUG}' is a reserved name for debug output: choose another name.")

        node = coerce_to_module(node)
        logger.debug(f"Adding node '{name}' ({node})")

        input_sockets = {
            name: create_node_socket(name, info)
            for name, info in node.input_schema().model_fields.items()
        }

        output_sockets = {
            name: create_node_socket(name, info)
            for name, info in node.output_schema().model_fields.items()
        }

        self.graph.add_node(
            name,
            instance=node,
            input_sockets=input_sockets,
            output_sockets=output_sockets,
            visits=0
        )

    def get_node(self, name: str) -> FlowNode:
        try:
            return self.graph.nodes[name]
        except KeyError as e:
            raise ValueError(f"Node named '{name}' not found in the flow.") from e

    def connect(self, source: str, target: str):
        source_node, source_socket_name = parse_connect_string(source)
        target_node, target_socket_name = parse_connect_string(target)

        source_sockets = self.get_node(source_node)['output_sockets']
        target_sockets = self.get_node(target_node)['input_sockets']

        source_socket: NodeSocket | None = None
        if source_socket_name:
            source_socket = source_sockets.get(source_socket_name, None)
            if not source_socket:
                raise FlowConnectError(
                    f"'{source}' does not exist. "
                    f"Output connections of '{source_node}' are: "
                    f"{', '.join(f'{sock.name} ({sock.annotation})' for sock in source_sockets.values())}"
                )

        target_socket: NodeSocket | None = None
        if target_socket_name:
            target_socket = target_sockets.get(target_socket_name, None)
            if not target_socket:
                raise FlowConnectError(
                    f"'{target}' does not exist. "
                    f"Input connections of '{target_node}' are: "
                    f"{', '.join(f'{sock.name} ({sock.annotation})' for sock in target_sockets.values())}"
                )

        source_socket_candidates: list[NodeSocket] = [source_socket] if source_socket else list(source_sockets.values())
        target_socket_candidates: list[NodeSocket] = [target_socket] if target_socket else list(target_sockets.values())

        possible_connections = [
            (source_cand, target_cand)
            for source_cand, target_cand in tproduct(source_socket_candidates, target_socket_candidates)
            if types_are_compatible(source_cand.annotation, target_cand.annotation)
        ]

        status = _connection_status(
            source_node,
            source_socket_candidates,
            target_node,
            target_socket_candidates
        )

        # There's no possible connection between these two nodes
        if not possible_connections:
            if len(source_socket_candidates) == len(target_socket_candidates) == 1:
                msg = (
                    f"Cannot connect '{source_node}.{source_socket_candidates[0].name}' "
                    f"with '{target_node}.{target_socket_candidates[0].name}': "
                    f"their declared input and output types do not match.\n{status}"
                )
            else:
                msg = (
                    f"Cannot connect '{source_node}' with '{target_node}': "
                    f"no matching connections available.\n{status}"
                )
            raise FlowConnectError(msg)

        # There's only one possible connection, use it
        if len(possible_connections) == 1:
            source_socket = possible_connections[0][0]
            target_socket = possible_connections[0][1]

        # There are multiple possible connections, let's try to match them by name
        if len(possible_connections) > 1:
            name_matches = [
                (in_sock, out_sock)
                for in_sock, out_sock in possible_connections
                if in_sock.name == out_sock.name
            ]
            # There are either no matches or more than one, we can't pick one reliably
            if len(name_matches) != 1:
                raise FlowConnectError(
                    f"Cannot connect '{source_node}' with '{target_node}': more than one connection is possible "
                    "between these nodes. Please specify the connection name, like: "
                    f"flow.connect('{source_node}.{possible_connections[0][0].name}', "
                    f"'{target_node}.{possible_connections[0][1].name}')."
                    f"\n{status}"
                )

            # Get the only possible match
            source_socket = name_matches[0][0]
            target_socket = name_matches[0][1]

        # Connection must be valid on both source/target sides
        if not source_node or not source_socket or not target_node or not target_socket:
            if source_node and source_socket:
                source_repr = f'{source_node}.{source_socket.name} ({source_socket.annotation})'
            else:
                source_repr = 'input needed'

            if target_node and target_socket:
                target_repr = f'({target_socket.annotation}) {target_node}.{target_socket.name}'
            else:
                target_repr = 'output'

            raise FlowConnectError(
                f'Connection must have both source and target: {source_repr} -> {target_repr}.'
            )

        if source_socket.name in target_socket.connected_to and target_socket.name in source_socket.connected_to:
            return

        if target_socket.connected_to and not target_socket.is_variadic:
            raise FlowConnectError(
                f"Cannot connect '{source_node}.{source_socket.name}' with '{target_node}.{target_socket.name}': "
                f"'{target_node}.{target_socket.name}' is already connected to {target_socket.connected_to}.\n"
            )

        source_socket.connected_to.append(target_node)
        target_socket.connected_to.append(source_node)

        logger.debug(f"Connecting '{source_node}.{source_socket.name}' to '{target_node}.{target_socket.name}'.")

        self.graph.add_edge(
            source_node,
            target_node,
            key=f'{source_socket.name}/{target_socket.name}',
            conn_type=source_socket.annotation,
            source_socket=source_socket,
            target_socket=target_socket,
            required=target_socket.required
        )

    def forward(self, data: RunFlow, **kwargs) -> Effect[FlowOutput]:
        return Effects.Sync(partial(self._invoke, data, **kwargs))

    def _invoke(self, data: RunFlow, **kwargs) -> FlowOutput:
        pass

def _connection_status(
    source_node: str,
    source_candidates: list[NodeSocket],
    target_node: str,
    target_candidates: list[NodeSocket]
) -> str:
    pass