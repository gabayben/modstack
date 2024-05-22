"""
Majority of credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/__init__.py
"""
from typing import Mapping, Optional, Sequence, Union

import networkx as nx

from modflow.channels import Channel
from modflow.checkpoints import Checkpointer
from modflow.contracts import FlowOutput, RunFlow
from modstack.modules import SerializableModule
from modstack.typing import Effect

class PregelBase:
    def __init__(self):
        self.graph = nx.MultiDiGraph()

class Pregel(SerializableModule[RunFlow, FlowOutput], PregelBase):
    channels: Mapping[str, Channel]
    input_channels: Union[str, Sequence[str]]
    output_channels: Union[str, Sequence[str]]
    stream_channels: Optional[Union[str, Sequence[str]]] = None
    checkpointer: Checkpointer

    def forward(self, data: RunFlow, **kwargs) -> Effect[FlowOutput]:
        pass