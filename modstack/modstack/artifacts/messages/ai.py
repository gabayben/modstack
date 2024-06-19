"""
Credit to LangChain - https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/messages/ai.py
"""

from typing import Literal, Optional, Union, override

from pydantic import Field

from modstack.artifacts.messages import MessageArtifact, MessageChunk, MessageType
from modstack.typing import InvalidToolCall, ToolCall, ToolCallChunk, UsageMetadata

class AiMessage(MessageArtifact):
    message_type: Literal[MessageType.AI]
    tool_calls: list[ToolCall] = Field(default_factory=list)
    invalid_tool_calls: list[InvalidToolCall] = Field(default_factory=list)
    usage_metadata: Optional[UsageMetadata] = None

    def __init__(
        self,
        content: str,
        tool_calls: list[ToolCall] = [],
        invalid_tool_calls: list[InvalidToolCall] = [],
        usage_metadata: Optional[UsageMetadata] = None,
        name: str | None = None,
        **kwargs
    ):
        super().__init__(
            content=content,
            message_type=MessageType.AI,
            tool_calls=tool_calls,
            invalid_tool_calls=invalid_tool_calls,
            usage_metadata=usage_metadata,
            name=name,
            **kwargs
        )

    @override
    def pretty_repr(self, html: bool = False, **kwargs) -> str:
        base = super().pretty_repr(html=html, **kwargs)
        lines = []

        def format_tool_args(tool_call: Union[ToolCall, InvalidToolCall]) -> list[str]:
            lines = [
                f'  {tool_call.get('name', 'Tool')} ({tool_call.get('id')})',
                f'  Call Id: {tool_call.get('id')}'
            ]
            if tool_call.get('error', None):
                lines.append(f'  Error: {tool_call.get('error')}')
            lines.append('  Args:')
            args = tool_call.get('args', None)
            if isinstance(args, str):
                lines.append(f'    {args}')
            elif isinstance(args, dict):
                for name, arg in args.items():
                    lines.append(f'    {name}: {arg}')
            return lines

        if self.tool_calls:
            lines.append('Tool Calls:')
            for tool_call in self.tool_calls:
                lines.extend(format_tool_args(tool_call))
        if self.invalid_tool_calls:
            lines.append('Invalid Tool Calls:')
            for tool_call in self.invalid_tool_calls:
                lines.extend(format_tool_args(tool_call))

        return f'{base.strip()}\n{'\n'.join(lines)}'.strip()

AiMessage.model_rebuild()

class AiMessageChunk(AiMessage, MessageChunk):
    tool_call_chunks: list[ToolCallChunk] = Field(default_factory=list)

    def __init__(
        self,
        content: str,
        tool_calls: list[ToolCall] = [],
        tool_call_chunks: list[ToolCallChunk] = [],
        invalid_tool_calls: list[InvalidToolCall] = [],
        usage_metadata: Optional[UsageMetadata] = None,
        name: str | None = None,
        **kwargs
    ):
        super().__init__(
            content=content,
            message_type=MessageType.AI,
            tool_calls=tool_calls,
            tool_call_chunks=tool_call_chunks,
            invalid_tool_calls=invalid_tool_calls,
            usage_metadata=usage_metadata,
            name=name,
            **kwargs
        )

    @override
    def __add__(self, other: Union[str, list[str], MessageChunk]) -> MessageChunk:
        pass