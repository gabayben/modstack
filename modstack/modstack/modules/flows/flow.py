from modstack.core import CommandHandler, Module
from modstack.modules.flows import NodeId

class Flow:
    @property
    def nodes(self) -> dict[NodeId, CommandHandler]:
        raise NotImplementedError()

    def __init__(self):
        self._nodes = {}

    def add_module(
        self, module: Module,
        name: str | None = None
    ) -> None:
        pass