from typing import Literal, Optional

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