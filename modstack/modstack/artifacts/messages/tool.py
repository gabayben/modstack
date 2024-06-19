from typing import Literal, Optional

from modstack.artifacts.messages import MessageArtifact, MessageChunk, MessageType

class ToolMessage(MessageArtifact):
    tool_call_id: str
    message_type: Literal[MessageType.TOOL]

    def __init__(
        self,
        content: str,
        tool_call_id: str,
        name: Optional[str] = None,
        role: Optional[str] = None
    ):
        super().__init__(
            content=content,
            message_type=MessageType.TOOL,
            name=name or tool_call_id,
            role=role or MessageType.TOOL
        )

ToolMessage.model_rebuild()

class ToolMessageChunk(ToolMessage, MessageChunk):
    pass