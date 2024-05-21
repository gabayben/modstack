import networkx as nx

from modflow.typing import FlowOutput, RunFlow
from modstack.modules import Modules

class PregelBase:
    def __init__(self):
        self.graph = nx.MultiDiGraph()

class Pregel(Modules.Sync[RunFlow, FlowOutput], PregelBase):
    def _invoke(self, data: RunFlow) -> FlowOutput:
        pass