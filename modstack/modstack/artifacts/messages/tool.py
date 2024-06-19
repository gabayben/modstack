"""
Credit to LangChain - https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/messages/tool.py
"""

from typing import Literal, Optional, Union, override

from modstack.artifacts.messages import MessageArtifact, MessageChunk, MessageType
from modstack.artifacts.messages.utils import merge_content
from modstack.utils.merge import merge_dicts

class ToolMessage(MessageArtifact):
    tool_call_id: str
    message_type: Literal[MessageType.TOOL]

    def __init__(
        self,
        content: str,
        tool_call_id: str,
        name: Optional[str] = None,
        role: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            content=content,
            message_type=MessageType.TOOL,
            name=name or tool_call_id,
            role=role or MessageType.TOOL,
            **kwargs
        )

ToolMessage.model_rebuild()

class ToolMessageChunk(ToolMessage, MessageChunk):
    @override
    def __add__(self, other: Union[str, list[str], MessageChunk]) -> MessageChunk:
        if isinstance(other, ToolMessageChunk):
            if self.tool_call_id != other.tool_call_id:
                raise ValueError('Cannot concatenate ToolMessageChunks with different names.')
            return self.__class__(
                content=merge_content(self.content, other.content),
                metadata=merge_dicts(self.metadata, other.metadata),
                **other.model_dump(exclude={'content', 'metadata'})
            )
        return super().__add__(other)