"""
Much of this code was taken from Haystack - https://github.com/deepset-ai/haystack/blob/main/haystack/core/pipeline/base.py
SPDX-FileCopyrightText: 2022-present deepset GmbH <info@deepset.ai>
SPDX-License-Identifier: Apache-2.0
"""

from functools import partial
import logging

import networkx as nx

from modstack.constants import DEBUG
from modstack.contracts.flows import FlowOutput, RunFlow
from modstack.modules import ModuleLike, SerializableModule, coerce_to_module
from modstack.modules.flows.typing import FlowNode
from modstack.modules.flows.utils import parse_connect_string
from modstack.typing import Effect, Effects

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

        input_schema = node.input_schema()
        output_schema = node.output_schema()

        self.graph.add_node(
            name,
            instance=node,
            input_sockets=input_schema.model_fields,
            output_sockets=output_schema.model_fields,
            visits=0
        )

    def get_node(self, name: str) -> FlowNode:
        try:
            return self.graph.nodes[name]
        except KeyError as e:
            raise ValueError(f"Node named '{name}' not found in the flow.") from e

    def connect(self, source: str, target: str):
        source_node, source_socket = parse_connect_string(source)
        target_node, target_socket = parse_connect_string(target)

        source_sockets = self.get_node(source_node)['output_sockets']
        target_sockets = self.get_node(target_node)['input_sockets']

    def forward(self, data: RunFlow, **kwargs) -> Effect[FlowOutput]:
        return Effects.Sync(partial(self._invoke, data, **kwargs))

    def _invoke(self, data: RunFlow, **kwargs) -> FlowOutput:
        pass