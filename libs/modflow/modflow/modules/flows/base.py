"""
Majority of credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/__init__.py
"""

import networkx as nx

from modflow.contracts import FlowOutput, RunFlow
from modstack.modules import SerializableModule
from modstack.typing import Effect

class PregelBase:
    def __init__(self):
        self.graph = nx.MultiDiGraph()

class Pregel(SerializableModule[RunFlow, FlowOutput], PregelBase):
    def forward(self, data: RunFlow, **kwargs) -> Effect[FlowOutput]:
        pass