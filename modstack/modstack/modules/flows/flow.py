"""
Much of this code was taken from Haystack - https://github.com/deepset-ai/haystack/blob/main/haystack/core/pipeline/pipeline.py
SPDX-FileCopyrightText: 2022-present deepset GmbH <info@deepset.ai>
SPDX-License-Identifier: Apache-2.0
"""

from functools import partial

from modstack.modules.flows import FlowBase, FlowData, RunFlow
from modstack.typing import Effect, Effects

class Flow(FlowBase):
    def forward(self, contract: RunFlow, **kwargs) -> Effect[FlowData]:
        return Effects.Sync(partial(self._invoke, contract, **kwargs))

    def _invoke(self, contract: RunFlow, **kwargs) -> FlowData:
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

        # this is what we'll return at the end
        final_outputs: FlowData = {}