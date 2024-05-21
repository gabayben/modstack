from modflow.typing import FlowData
from modstack.typing import Serializable

class RunFlow(Serializable):
    node_id: str | None = None
    initial_state: FlowData | None = None

    def __init__(
        self,
        node_id: str | None = None,
        initial_state: FlowData | None = None
    ):
        super().__init__(node_id=node_id, initial_state=initial_state)