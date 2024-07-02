import asyncio
from functools import partial
import json
from typing import Any, Iterable, Optional, final

from modstack.artifacts.messages import AiMessage, MessageArtifact, ToolMessage
from modstack.core import Module, SerializableModule
from modstack.typing import Effect, Effects, ToolCall
from modstack.utils.threading import get_executor

class ToolExecutor(SerializableModule[MessageArtifact, list[ToolMessage]]):
    tools: dict[str, Module]

    def __init__(
        self,
        tools: list[Module],
        name: str = 'tools',
        tags: Optional[list[str]] = None,
        **kwargs
    ):
        super().__init__(name=name, tags=tags, **kwargs)
        self.tools = {tool.get_name(): tool for tool in tools}

    @final
    def forward(self, message: MessageArtifact, **kwargs) -> Effect[list[ToolMessage]]:
        return Effects.From(
            invoke=partial(self._invoke, message, **kwargs),
            ainvoke=partial(self._ainvoke, message, **kwargs)
        )

    def _invoke(self, message: MessageArtifact, **kwargs) -> list[ToolMessage]:
        if not isinstance(message, AiMessage):
            raise ValueError('Provided message is not an AiMessage.')

        def run(tool_call: ToolCall) -> ToolMessage:
            output = self.tools[tool_call['name']].invoke(tool_call['args'], **kwargs)
            return ToolMessage(
                content=_str_output(output),
                name=tool_call['name'],
                tool_call_id=tool_call['id']
            )

        with get_executor() as executor:
            return [*executor.map(run, message.tool_calls)]

    async def _ainvoke(self, message: MessageArtifact, **kwargs) -> list[ToolMessage]:
        if not isinstance(message, AiMessage):
            raise ValueError('Provided message is not an AiMessage.')

        async def arun(tool_call: ToolCall) -> ToolMessage:
            output = await self.tools[tool_call['name']].ainvoke(tool_call['args'], **kwargs)
            return ToolMessage(
                content=_str_output(output),
                name=tool_call['name'],
                tool_call_id=tool_call['id']
            )

        return list(
            await asyncio.gather(*(arun(tool_call) for tool_call in message.tool_calls))
        )

def _str_output(output: Any) -> str:
    if isinstance(output, Iterable):
        try:
            return json.dumps(output)
        except BaseException:
            pass
    return str(output)