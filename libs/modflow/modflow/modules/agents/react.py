from typing import Optional, Sequence

from modflow import FlowInput, FlowOutput
from modflow.checkpoints import Checkpointer
from modstack.artifacts.messages import MessageArtifact
from modstack.modules import Module, ModuleLike, SerializableModule
from modstack.modules.ai import AgenticLLMRequest

def create_react_agent(
    model: Module[AgenticLLMRequest, MessageArtifact],
    tools: list[ModuleLike],
    checkpointer: Optional[Checkpointer] = None,
    interrupt_before: Optional[Sequence[str]] = None,
    interrupt_after: Optional[Sequence[str]] = None,
    debug: bool = False
) -> SerializableModule[FlowInput, FlowOutput]:
    pass