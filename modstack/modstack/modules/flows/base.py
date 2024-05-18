from abc import ABC
import logging

import networkx as nx

from modstack.contracts.flows import SocketId
from modstack.modules import Module
from modstack.modules.flows import FlowConnectError, FlowError, FlowNode, FlowSocket, NodeNotFound
from modstack.utils.func import tproduct
from modstack.utils.reflection import types_are_compatible

logger = logging.getLogger(__name__)

class FlowBase(Module, ABC):
    def __init__(self):
        super().__init__()
        self.graph = nx.MultiDiGraph()

    def connect(
        self,
        source: SocketId,
        target: SocketId
    ) -> None:
        self.validate_context()

        if source.node == target.node:
            raise FlowError(f'Source and target node are both {target.node}. Cannot connect node to itself.')

        source_schema = self._get_or_add_node(source.node)['output_sockets']
        target_schema = self._get_or_add_node(target.node)['input_sockets']
        source_field = self._get_field_info(source.node, source_schema, source.field)
        target_field = self._get_field_info(target.node, target_schema, target.field)

        source_candidates: list[FlowSocket] = [source_field] if source_field else list(source_schema.values())
        target_candidates: list[FlowSocket] = [target_field] if target_field else list(target_schema.values())

        possible_connections = [
            (source_cand, target_cand)
            for source_cand, target_cand in tproduct(source_candidates, target_candidates)
            if types_are_compatible(source_cand.field.annotation, target_cand.field.annotation)
        ]

        status = _connection_status(source.node, source_candidates, target.node, target_candidates)

        if not possible_connections:
            if len(source_candidates) == len(target_candidates) == 1:
                msg = (
                    f'Cannot connect {source.node}/{source_candidates[0].name} with {target.node}/{target_candidates[0].name}: '
                    f'there declared input and output types do not match.\n{status}'
                )
            else:
                msg = (
                    f'Cannot connect {source.node} with {target.node}: '
                    f'no matching connections available.\n{status}'
                )
            raise FlowConnectError(msg)

        if len(possible_connections) == 1:
            source_socket = possible_connections[0][0]
            target_socket = possible_connections[0][1]

        if len(possible_connections) > 1:
            name_matches = [
                (source_cand, target_cand)
                for source_cand, target_cand in possible_connections
                if source_cand.name == target_cand.name
            ]
            if len(name_matches) != 1:
                raise FlowConnectError(
                    f"Cannot connect '{source.node}' with '{target.node}': more than one connection is possible "
                    "between these nodes. Please specify the field names, like:\n"
                    f"flow.connect(\n('{source.node}', '{name_matches[0][0].name}'),\n"
                    f"('{target.node}', '{name_matches[0][1].name}')\n).\n{status}"
                )
            source_socket = name_matches[0][0]
            target_socket = name_matches[0][1]

        if not source_socket or not target_socket:
            if source_socket:
                source_repr = f'{source.node}/{source_socket.name} ({source_socket.field.annotation})'
            else:
                source_repr = 'input needed'
            if target_socket:
                target_repr = f'({target_socket.field.annotation}) {target.node}/{target_socket.name}'
            else:
                target_repr = 'output'
            raise FlowConnectError(f'Connection must have both source and target: {source_repr} -> {target_repr}.')

        logger.debug(f"Connecting '{source.node}/{source_socket.name}' to '{target.node}/{target_socket.name}'.")

        if source.node in target_socket.connections and target.node in source_socket.connections:
            return

        source_socket.connections.append(target.node)
        target_socket.connections.append(source.node)

        self.graph.add_edge(
            source.node,
            target.node,
            key=f'{source_socket.name}/{target_socket.name}',
            source_socket=source_socket,
            target_socket=target_socket,
            connection_type=source_socket.field.annotation
        )

    def get_node(self, path: str) -> FlowNode:
        if not self.graph.has_node(path):
            raise NodeNotFound(f'Node with path {path} not found in graph.')
        return self.graph.nodes[path]

    def _get_or_add_node(self, path: str) -> FlowNode:
        if not self.graph.has_node(path):
            endpoint = self.context.get_endpoint(path)
            node = FlowNode(
                name=path,
                instance=endpoint,
                input_sockets={field: FlowSocket(field, info, []) for field, info in endpoint.input_schema.model_fields.items()},
                output_sockets={field: FlowSocket(field, info, []) for field, info in endpoint.output_schema.model_fields.items()},
                visits=0
            )
            self.graph.add_node(path, **node)
            return node
        return self.graph.nodes[path]

    def _get_field_info(self, node: str, sockets: dict[str, FlowSocket], field: str | None) -> FlowSocket | None:
        if field:
            socket = sockets.get(field, None)
            if not socket:
                raise FlowConnectError(f'Field {field} not found for node {node}.')
            return socket
        elif len(sockets) == 1:
            return list(sockets.values())[0]
        return None

def _connection_status(
    source: str,
    source_sockets: list[FlowSocket],
    target: str,
    target_sockets: list[FlowSocket]
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

    return f"'{source}':\n{source_sockets_list}\n'{target}':\n{target_sockets_list}"