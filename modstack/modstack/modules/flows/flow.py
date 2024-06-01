"""
Much of this code was taken from Haystack - https://github.com/deepset-ai/haystack/blob/main/haystack/core/pipeline/pipeline.py
SPDX-FileCopyrightText: 2022-present deepset GmbH <info@deepset.ai>
SPDX-License-Identifier: Apache-2.0
"""
from copy import deepcopy
from functools import partial
import logging
from typing import cast

from modstack.exceptions import FlowMaxLoops
from modstack.modules import Module
from modstack.modules.flows import FlowBase, FlowData, RunFlow
from modstack.tracing import Span, Tracer, global_tracer
from modstack.typing import Effect, Effects

logger = logging.getLogger(__name__)

class Flow(FlowBase):
    def forward(self, contract: RunFlow, **kwargs) -> Effect[FlowData]:
        return Effects.Sync(partial(self._invoke, contract, **kwargs))

    def _invoke(
        self,
        contract: RunFlow,
        tracer: Tracer = global_tracer,
        **kwargs
    ) -> FlowData:
        # reset the visits count for each node
        self._init_graph()

        # normalize data
        data = self._match_flow_inputs(contract.data)

        # Raise if input is malformed in some way
        self._validate_inputs(data)

        # Initialize the inputs state
        last_inputs = self._init_inputs_state(data)

        # Take all nodes that have at least 1 input not connected or is variadic,
        # and all nodes that have no inputs at all
        to_run = self._init_to_run()

        # These variables are used to detect when we're stuck in a loop.
        # Stuck loops can happen when one or more nodes are waiting for input but
        # no other node is going to run.
        # This can happen when a whole branch of the graph is skipped for example.
        # When we find that there are two consecutive iterations of the loop where waiting_for_input is the same,
        # we know we're stuck in a loop and we can't make any progress.
        before_last_waiting_for_input: set[str] | None = None
        last_waiting_for_input: set[str] | None = None

        # The waiting_for_input list is used to keep track of nodes that are waiting for input
        waiting_for_input: list[tuple[str, Module]] = []

        include_outputs_from = contract.include_outputs_from if contract.include_outputs_from is not None else set[str]()

        # this is what we'll return at the end
        final_outputs: FlowData = {}

        with tracer.trace(
            'modstack.flow.invoke',
            {
                'modstack.flow.input_data': data,
                'modstack.flow.output_data': final_outputs,
                'modstack.flow.debug': contract.debug,
                'modstack.flow.metadata': self.metadata,
                'modstack.flow.max_loops_allowed': self.max_loops_allowed
            }
        ):
            extra_outputs: FlowData = {}

            while len(to_run) > 0:
                node, instance = to_run.pop(0)
                node_data = self.get_node(node)

                if (
                    any(socket.is_variadic for socket in node_data['input_sockets'].values())
                    and not node_data['is_greedy']
                ):
                    there_are_non_variadics = False
                    for other_node, other_instance in to_run:
                        other_node_data = self.get_node(other_node)
                        if any(not socket.is_variadic for socket in other_node_data['input_sockets'].values()):
                            there_are_non_variadics = True
                            break

                    if there_are_non_variadics:
                        if (node, instance) not in waiting_for_input:
                            waiting_for_input.append((node, instance))
                        continue

                    if node in last_inputs and len(node_data['input_sockets']) == len(last_inputs[node]):
                        if node_data['visits'] > self.max_loops_allowed:
                            raise FlowMaxLoops(
                                f"Maximum loops count ({self.max_loops_allowed}) exceeded for node '{node}'."
                            )
                        # This node has all the inputs it needs to run
                        with tracer.trace(
                            'modstack.flow.invoke',
                            {
                                'modstack.node.name': node,
                                'modstack.node.type': instance.__class__.__name__,
                                'modstack.node.input_types': {
                                    k: type(v).__name__ for k, v in last_inputs[node].items()
                                },
                                'modstack.node.input_spec': {
                                    key: {
                                        'type': socket.annotation.__name__ if isinstance(socket.annotation, type) else str(socket.annotation),
                                        'connections': socket.connections
                                    }
                                    for key, socket in node_data['input_sockets'].items()
                                },
                                'modstack.node.output_spec': {
                                    key: {
                                        'type': socket.annotation.__name__ if isinstance(socket.annotation, type) else str(socket.annotation)
                                    }
                                    for key, socket in node_data['output_sockets'].items()
                                }
                            }
                        ) as span:
                            span = cast(Span, span)
                            span.set_content_tag('modstack.node.input', last_inputs[node])
                            logger.info(f'Running node {node}.')
                            result = instance.invoke(instance.construct_input(last_inputs[node]))
                            result = instance.construct_output(result)
                            self.graph.nodes[node]['visits'] += 1

                            span.set_tag('modstack.node.visits', self.graph.nodes[node]['visits'])
                            span.set_content_tag('modstack.node.output', result)

                            if node in contract.include_outputs_from:
                                extra_outputs[node] = deepcopy(result)

                        # Reset the waiting for input previous states, we managed to run a node
                        before_last_waiting_for_input = None
                        last_waiting_for_input = None

                        if (node, instance) in waiting_for_input:
                            # We manage to run this node that was in the waiting list, we can remove it.
                            # This happens when a node was put in the waiting list but we reached it from another edge.
                            waiting_for_input.remove((node, instance))

                        # We keep track of which keys to remove from the result at the end of the loop.
                        # This is done after the output has been distributed to the next nodes, so that
                        # we're sure all nodes that need this output have received it.
                        to_remove_from_result = set[str]()
                        for source_node, target_node, edge_data in self.get_edges():
                            if target_node == node and edge_data['target_socket'].is_variadic:
                                # Delete variadic inputs that were already consumed
                                last_inputs[node][edge_data['target_socket'].name] = []

                            if source_node != node:
                                continue

                            if edge_data['source_socket'].name not in result:
                                # This output has not been produced by the node, skip it
                                continue

                            if target_node not in last_inputs:
                                last_inputs[target_node] = {}
                            to_remove_from_result.add(edge_data['source_socket'].name)
                            value = result[edge_data['source_socket'].name]

                            if edge_data['target_socket'].is_variadic:
                                if edge_data['target_socket'].name not in last_inputs[target_node]:
                                    last_inputs[target_node][edge_data['target_socket'].name] = []
                                # Add to the list of variadic inputs
                                last_inputs[target_node][edge_data['target_socket'].name].append(value)
                            else:
                                last_inputs[target_node][edge_data['target_socket'].name] = value