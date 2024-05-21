from modflow.typing import FlowData
from modstack.contracts import Contract

class RunFlow(Contract):
    initial_state: FlowData | None = None

    def __init__(
        self,
        initial_state: FlowData | None = None
    ):
        super().__init__(initial_state=initial_state)