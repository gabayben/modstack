from typing import Any, Type

from modstack.commands import Command, CommandId

class SocketId(CommandId):
    field: str | None = None

FlowInput = dict[Type[Command] | CommandId, dict[str, Any]]
FlowOutput = dict[Type[Command] | CommandId, Any]

class RunFlow(Command[FlowOutput]):
    node: CommandId | None = None
    data: FlowInput | None = None

    def __init__(
        self,
        node: CommandId | None = None,
        data: FlowInput | None = None,
        **kwargs
    ):
        super().__init__(node=node, data=data, **kwargs)

    @classmethod
    def name(cls) -> str:
        return 'run_flow'