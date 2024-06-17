"""
Credit to Haystack - https://github.com/deepset-ai/haystack/blob/main/haystack/core/pipeline/pipeline.py
SPDX-FileCopyrightText: 2022-present deepset GmbH <info@deepset.ai>
SPDX-License-Identifier: Apache-2.0
"""

from copy import deepcopy
from functools import partial
import logging
from typing import Unpack, cast

from modstack.exceptions import FlowMaxLoops
from modstack.modules import Module
from modstack.modules.flows import FlowBase, FlowData, FlowInput, RunFlow
from modstack.tracing import Span, Tracer, global_tracer
from modstack.typing import Effect, Effects

logger = logging.getLogger(__name__)

class Flow(FlowBase):
    def forward(self, inputs: FlowInput, **kwargs) -> Effect[FlowData]:
        return Effects.Sync(partial(self._invoke, inputs, **kwargs))

    def _invoke(
        self,
        inputs: FlowInput,
        tracer: Tracer = global_tracer,
        **kwargs: Unpack[RunFlow]
    ) -> FlowData:
        tracer = kwargs['tracer'] or global_tracer

        # reset the visits count for each node
        self._init_graph()

        # normalize data
        data = self._match_flow_inputs(inputs)

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

        include_outputs_from = kwargs['include_outputs_from'] if kwargs['include_outputs_from'] is not None else set[str]()

        # this is what we'll return at the end
        final_outputs: FlowData = {}

        with tracer.trace(
            'modstack.flow.invoke',
            {
                'modstack.flow.input_data': data,
                'modstack.flow.output_data': final_outputs,
                'modstack.flow.debug': kwargs['debug'],
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

                            if node in kwargs['include_outputs_from']:
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

                            target_node_data = self.get_node(target_node)
                            pair = (target_node, target_node_data['instance'])
                            if target_node_data['is_greedy'] and edge_data['target_socket'].is_variadic:
                                # If the target is greedy, we can run it right away.
                                # First we remove it from the lists it's in if it's there or we risk running it multiple times.
                                if pair in waiting_for_input:
                                    waiting_for_input.remove(pair)
                                if pair in to_run:
                                    to_run.remove(pair)
                                to_run.append(pair)
                            if pair not in waiting_for_input and pair not in to_run:
                                to_run.append(pair)

                            result = {k: v for k, v in result.items() if k not in to_remove_from_result}

                            if len(result) > 0:
                                final_outputs[node] = result
                    else:
                        # This node doesn't have enough inputs so we can't run it yet
                        if (node, instance) not in waiting_for_input:
                            waiting_for_input.append((node, instance))

                    if len(to_run) == 0 and len(waiting_for_input) > 0:
                        # Check if we're stuck in a loop.
                        # It's important to check whether previous waitings are None as it could be that no
                        # node has actually been run yet.
                        if (
                            before_last_waiting_for_input is not None
                            and last_waiting_for_input is not None
                            and before_last_waiting_for_input == last_waiting_for_input
                        ):
                            # Are we actually stuck or there's a lazy variadic or a node that has only default inputs waiting for input?
                            # This is our last resort, if there's no lazy variadic or node with only default inputs waiting for input
                            # then we're stuck for real and we can't make any progress.
                            before_last_waiting_for_input = (
                                last_waiting_for_input.copy()
                                if last_waiting_for_input is not None
                                else None
                            )
                            last_waiting_for_input = {item[0] for item in waiting_for_input}

                            # Remove from waiting only if there is actually enough input to run
                            for node, instance in waiting_for_input:
                                node_data = self.get_node(node)

                                if node not in last_inputs:
                                    last_inputs[node] = {}

                                # Lazy variadics must be removed only if there's nothing else to run at this stage
                                is_variadic = any(socket.is_variadic for socket in node_data['input_sockets'].values())
                                if is_variadic and not node_data['is_greedy']:
                                    there_are_only_lazy_variadics = True
                                    for other_node, other_instance in waiting_for_input:
                                        if other_node == node:
                                            continue
                                        other_node_data = self.get_node(other_node)
                                        there_are_only_lazy_variadics &= (
                                            any(socket.is_variadic for socket in other_node_data['input_sockets'].values())
                                            and not other_node_data['is_greedy']
                                        )
                                    if not there_are_only_lazy_variadics:
                                        continue

                                # Nodes that have defaults for all their inputs must be treated the same identical way as we treat
                                # lazy variadic nodes. If there are only nodes with defaults we can run them.
                                # If we don't do this the order of execution of the Flow's nodes will be affected cause we
                                # enqueue the nodes in `to_run` at the start using the order they are added in the Flow.
                                # If a node A with defaults is added before a node B that has no defaults, but in the Flow
                                # logic A must be executed after B it could instead run before if we don't do this check.
                                has_only_defaults = all(not socket.required for socket in node_data['input_sockets'].values())
                                if has_only_defaults:
                                    there_are_only_defaults = True
                                    for other_node, other_instance in waiting_for_input:
                                        if other_node == node:
                                            continue
                                        other_node_data = self.get_node(other_node)
                                        there_are_only_defaults &= all(not socket.required for socket in other_node_data['input_sockets'].values())
                                    if not there_are_only_defaults:
                                        continue

                                # Find the first node that has all the inputs it needs to run
                                has_enough_inputs = True
                                for input_socket in node_data['input_sockets'].values():
                                    if input_socket.required and input_socket.name not in last_inputs[node]:
                                        has_enough_inputs = False
                                        break
                                    if input_socket.required:
                                        continue
                                    if input_socket.name not in last_inputs[node]:
                                        last_inputs[node][input_socket.name] = input_socket.default
                                if has_enough_inputs:
                                    break

                            waiting_for_input.remove((node, instance))
                            to_run.append((node, instance))

            if len(include_outputs_from) > 0:
                for node, output in extra_outputs.items():
                    inner = final_outputs.get(node, None)
                    if inner is None:
                        final_outputs[node] = output
                    else:
                        # Let's not override any keys that are already
                        # in the final_outputs as they might be different
                        # from what we cached in extra_outputs, e.g. when loops
                        # are involved.
                        for k, v in output.items():
                            if k not in inner:
                                inner[k] = v

            return final_outputs