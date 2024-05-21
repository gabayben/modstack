from typing import Iterable

from modstack.contracts.agents import AgentRequest
from modstack.modules import Modules
from modstack.modules.agents import Agent
from modstack.typing import ChatMessage

class ReactAgent(Modules.Sync[AgentRequest, Iterable[ChatMessage]], Agent):
    def _invoke(self, data: AgentRequest, **kwargs) -> Iterable[ChatMessage]:
        pass