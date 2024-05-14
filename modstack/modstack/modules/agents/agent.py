from typing import NamedTuple, Type

from modstack.commands import Command, CommandHandler
from modstack.modules import Module

class ToolId(NamedTuple):
    command: Type[Command]
    module: str | None = None

class Agent(Module):
    @property
    def modules(self) -> list[Module]:
        pass

    @property
    def tools(self) -> dict[ToolId, CommandHandler]:
        pass