from typing import Literal

from modstack.artifacts.messages import MessageArtifact, MessageChunk, MessageType

class HumanMessage(MessageArtifact):
    message_type: Literal[MessageType.HUMAN]

    def __init__(
        self,
        content: str,
        name: str | None = None,
        **kwargs
    ):
        _ = kwargs.pop('role', None)
        super().__init__(content, MessageType.HUMAN, name=name, **kwargs)

HumanMessage.model_rebuild()

class HumanMessageChunk(HumanMessage, MessageChunk):
    pass