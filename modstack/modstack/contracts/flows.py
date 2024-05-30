from typing import Any

from pydantic import Field

from modstack.typing import Serializable

FlowInput = dict[str, Any]
FlowOutput = dict[str, dict[str, Any]]

class RunFlow(Serializable):
    data: FlowInput = Field(default_factory=dict)
    include_outputs_from: set[str] | None = None