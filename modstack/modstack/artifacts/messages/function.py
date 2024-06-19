from typing import Literal

from modstack.artifacts.messages import MessageArtifact, MessageChunk, MessageType

class FunctionMessage(MessageArtifact):
    message_type: Literal[MessageType.FUNCTION]

    def __init__(
        self,
        content: str,
        name: str | None = None,
        **kwargs
    ):
        super().__init__(content, MessageType.FUNCTION, name=name, **kwargs)

FunctionMessage.model_rebuild()

class FunctionMessageChunk(FunctionMessage, MessageChunk):
    pass