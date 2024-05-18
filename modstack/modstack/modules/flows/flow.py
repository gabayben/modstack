from modstack.contracts.flows import FlowInput, FlowOutput
from modstack.endpoints import endpoint
from modstack.modules.flows import FlowBase

class Flow(FlowBase):
    @endpoint
    def run(
        self,
        node_id: str | None = None,
        data: FlowInput | None = None,
        **kwargs
    ) -> FlowOutput:
        pass