from modstack.contracts.flows import FlowOutput, RunFlow
from modstack.modules import Modules
from modstack.modules.flows.base import FlowBase

class Flow(Modules.Sync[RunFlow, FlowOutput], FlowBase):
    def _invoke(self, data: RunFlow) -> FlowOutput:
        pass