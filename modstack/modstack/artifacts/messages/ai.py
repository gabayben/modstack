"""
Credit to LangChain - https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/messages/ai.py
"""

import json
from typing import Literal, Optional, Self, Union, override

from pydantic import Field, model_validator

from modstack.artifacts.messages import MessageArtifact, MessageChunk, MessageType
from modstack.artifacts.messages.utils import merge_content
from modstack.typing import InvalidToolCall, ToolCall, ToolCallChunk, UsageMetadata
from modstack.utils.json import parse_partial_json
from modstack.utils.merge import merge_dicts, merge_lists

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
        if isinstance(other, AiMessageChunk):
            content = merge_content(self.content, other.content)
            metadata = merge_dicts(self.metadata, other.metadata)

            # Merge tool call chunks
            if self.tool_call_chunks or other.tool_call_chunks:
                raw_tool_calls = merge_lists(self.tool_call_chunks, other.tool_call_chunks)
                if raw_tool_calls:
                    tool_call_chunks = [
                        ToolCallChunk(
                            name=tool_call.get('name'),
                            args=tool_call.get('args'),
                            id=tool_call.get('id'),
                            index=tool_call.get('index')
                        )
                        for tool_call in raw_tool_calls
                    ]
                else:
                    tool_call_chunks = []
            else:
                tool_call_chunks = []

            # Token usage
            if self.usage_metadata or other.usage_metadata:
                left = self.usage_metadata or UsageMetadata(input_tokens=0, output_tokens=0, total_tokens=0)
                right = other.usage_metadata or UsageMetadata(input_tokens=0, output_tokens=0, total_tokens=0)
                usage_metadata = UsageMetadata(
                    input_tokens=left['input_tokens'] + right['input_tokens'],
                    output_tokens=left['output_tokens'] + right['output_tokens'],
                    total_tokens=left['total_tokens'] + right['total_tokens']
                )
            else:
                usage_metadata = None

            return self.__class__(
                content=content,
                metadata=metadata,
                tool_call_chunks=tool_call_chunks,
                usage_metadata=usage_metadata,
                **self.model_dump(exclude={'content', 'metadata', 'tool_call_chunks', 'usage_metadata'})
            )

        return super().__add__(other)

    @model_validator(mode='after')
    def init_tool_calls(self) -> Self:
        if not self.tool_call_chunks:
            if self.tool_calls:
                self.tool_call_chunks = [
                    ToolCallChunk(
                        name=tool_call['name'],
                        args=json.dumps(tool_call['args']),
                        id=tool_call['id']
                    )
                    for tool_call in self.tool_calls
                ]
            if self.invalid_tool_calls:
                tool_call_chunks = self.tool_call_chunks or []
                tool_call_chunks.extend([
                    ToolCallChunk(
                        name=tool_call['name'],
                        args=tool_call['args'],
                        id=tool_call['id']
                    )
                    for tool_call in self.invalid_tool_calls
                ])
                self.tool_call_chunks = tool_call_chunks
            return self

        tool_calls = []
        invalid_tool_calls = []
        for chunk in self.tool_call_chunks:
            try:
                args_ = parse_partial_json(chunk['args'])
                if isinstance(args_, dict):
                    tool_calls.append(
                        ToolCall(
                            name=chunk['name'] or '',
                            args=args_,
                            id=chunk['id']
                        )
                    )
                else:
                    raise ValueError('Malformed args.')
            except BaseException as e:
                invalid_tool_calls.append(
                    InvalidToolCall(
                        name=chunk['name'],
                        args=chunk['args'],
                        id=chunk['id'],
                        error=None
                    )
                )
        self.tool_calls = tool_calls
        self.invalid_tool_calls = invalid_tool_calls
        return self