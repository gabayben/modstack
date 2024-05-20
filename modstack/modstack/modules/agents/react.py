from typing import Iterable

from modstack.contracts.agents import CallAgent
from modstack.modules import Modules
from modstack.modules.agents import Agent
from modstack.typing import ChatMessage

class ReactAgent(Modules.Sync[CallAgent, Iterable[ChatMessage]], Agent):
    def _invoke(self, data: CallAgent) -> Iterable[ChatMessage]:
        pass