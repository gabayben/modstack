from modstack.contracts.flows import FlowInput, FlowOutput
from modstack.endpoints import endpoint
from modstack.modules.flows.base import FlowBase

class Flow(FlowBase):
    @endpoint
    def run(
        self,
        node_id: str | None = None,
        data: FlowInput | None = None,
    ) -> FlowOutput:
        self.validate_context()
        return {}