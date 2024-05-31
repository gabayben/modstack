"""
Much of this code was taken from Haystack - https://github.com/deepset-ai/haystack/blob/main/haystack/core/pipeline/base.py
SPDX-FileCopyrightText: 2022-present deepset GmbH <info@deepset.ai>
SPDX-License-Identifier: Apache-2.0
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from copy import copy, deepcopy
import logging
from typing import Any, Iterator

import networkx as nx

from modstack.constants import DEBUG
from modstack.exceptions import FlowConnectError
from modstack.modules import Module, ModuleLike, SerializableModule, coerce_to_module
from modstack.modules.flows import FlowData, FlowInput, FlowSocketDescriptions, NodeSocket, NodeSocketDescription, RunFlow
from modstack.modules.flows.typing import FlowNode
from modstack.modules.flows.utils import create_node_socket, find_flow_inputs, find_flow_outputs, parse_connect_string, types_are_compatible
from modstack.typing import Effect
from modstack.utils.func import tproduct

logger = logging.getLogger(__name__)

class FlowBase(SerializableModule[RunFlow, FlowData], ABC):
    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def inputs(self, include_connected: bool = False) -> FlowSocketDescriptions:
        inputs: FlowSocketDescriptions = {}
        for node, sockets in find_flow_inputs(self.graph, include_connected=include_connected).items():
            socket_descriptions: dict[socket, NodeSocketDescription] = {}
            for socket in sockets:
                socket_descriptions[socket.name] = {'annotation': socket.annotation, 'required': socket.required}
                if not socket.required:
                    socket_descriptions[socket.name]['default'] = socket.default
            if socket_descriptions:
                inputs[node] = socket_descriptions
        return inputs

    def outputs(self, include_connected: bool = False) -> FlowSocketDescriptions:
        return {
            node: {
                socket.name: NodeSocketDescription(annotation=socket.annotation)
                for socket in sockets
            }
            for node, sockets in find_flow_outputs(self.graph, include_connected=include_connected).items()
            if sockets
        }

    def get_node(self, name: str) -> FlowNode:
        try:
            return self.graph.nodes[name]
        except KeyError as e:
            raise ValueError(f"Node named '{name}' not found in the flow.") from e

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

    def connect(self, source: str, target: str) -> None:
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

        status = _connections_status(
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

        if source_socket.name in target_socket.connections and target_socket.name in source_socket.connections:
            return

        if target_socket.connections and not target_socket.is_variadic:
            raise FlowConnectError(
                f"Cannot connect '{source_node}.{source_socket.name}' with '{target_node}.{target_socket.name}': "
                f"'{target_node}.{target_socket.name}' is already connected to {target_socket.connections}.\n"
            )

        source_socket.connections.append(target_node)
        target_socket.connections.append(source_node)

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

    def walk(self) -> Iterator[tuple[str, Module]]:
        for node, instance in self.graph.nodes(data='instance'):
            yield node, instance

    @abstractmethod
    def forward(self, data: RunFlow, **kwargs) -> Effect[FlowData]:
        pass

    def _init_graph(self) -> None:
        for node in self.graph.nodes:
            self.graph.nodes[node]['visits'] = 0

    def _match_flow_inputs(self, data: FlowInput) -> FlowData:
        """
        Prepares input data for flow nodes.

        Organizes input data for flow nodes and identifies any inputs that are not matched to any
        node's input slots. Deep-copies data items to avoid sharing mutables across multiple nodes.

        This method processes a flat dictionary of input data, where each key-value pair represents an input name
        and its corresponding value. It distributes these inputs to the appropriate flow nodes based on
        their input requirements. Inputs that don't match any node's input slots are classified as unresolved.
        """
        is_nested_inputs = all(isinstance(value, dict) for value in data.values())
        if not is_nested_inputs:
            # flat input, a dict where keys are input names and values are the corresponding values
            # we need to convert it to a nested dictionary of node inputs and then run the flow
            # just like in the previous case
            flow_inputs: FlowData = defaultdict(dict)
            unresolved_inputs: dict[str, Any] = {}

            # Retrieve the input slots for each node in the flow
            available_inputs = self.inputs()

            # Go through all provided to distribute them to the appropriate node inputs
            for name, value in data.items():
                resolved_at_least_once = False

                # Check each node to see if it has a slot for the current input
                for node, inputs in available_inputs.items():
                    if name in inputs:
                        # If a match is found, add the input to the node's input data
                        flow_inputs[node][name] = value
                        resolved_at_least_once = True

                if not resolved_at_least_once:
                    unresolved_inputs[name] = value

            if unresolved_inputs:
                logger.warning(
                    f'Inputs {list(unresolved_inputs.keys())} were not matched to any node inputs. '
                    'Please check your run parameters.'
                )

            data = dict(flow_inputs)

        for node, inputs in data.items():
            data[node] = {k: deepcopy(v) for k, v in inputs.items()}

        return data

    def _validate_inputs(self, data: FlowData) -> None:
        pass

    def _init_inputs_state(self, data: FlowData) -> FlowData:
        for node, inputs in data.items():
            if not self.graph.has_node(node):
                continue
            input_sockets = self.get_node(node)['input_sockets']
            for name, value in inputs.items():
                data[node][name] = copy(value)
                if input_sockets[name].is_variadic:
                    data[node][name] = [value]
        return {**data}

    def _init_to_run(self) -> list[tuple[str, Module]]:
        to_run: list[tuple[str, Module]] = []
        for node in self.graph.nodes:
            data = self.get_node(node)
            if len(data['input_sockets']) == 0:
                # Component has no input, can run right away
                to_run.append((node, data['instance']))
                continue
            for socket in data['input_sockets'].values():
                if socket.is_variadic or not socket.connections:
                    to_run.append((node, data['instance']))
                    break
        return to_run

def _connections_status(
    source_node: str,
    source_sockets: list[NodeSocket],
    target_node: str,
    target_sockets: list[NodeSocket]
) -> str:
    source_socket_entries = []
    for source_socket in source_sockets:
        source_socket_entries.append(f' - {source_socket.name}: {source_socket.field.annotation}')
    source_sockets_list = '\n'.join(source_socket_entries)

    target_socket_entries = []
    for target_socket in target_sockets:
        if target_socket.connections:
            source_status = f'sent by {', '.join(target_socket.connections)}'
        else:
            source_status = 'available'
        target_socket_entries.append(
            f' - {target_socket.name}: {target_socket.field.annotation} ({source_status})'
        )
    target_sockets_list = "\n".join(target_socket_entries)

    return f"'{source_node}':\n{source_sockets_list}\n'{target_node}':\n{target_sockets_list}"