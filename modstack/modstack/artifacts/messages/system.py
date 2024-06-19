from typing import Literal

from modstack.artifacts.messages import MessageArtifact, MessageChunk, MessageType

class SystemMessage(MessageArtifact):
    message_type: Literal[MessageType.SYSTEM]

    def __init__(
        self,
        content: str,
        name: str | None = None,
        **kwargs
    ):
        super().__init__(content, MessageType.SYSTEM, name=name, **kwargs)

SystemMessage.model_rebuild()

class SystemMessageChunk(SystemMessage, MessageChunk):
    pass