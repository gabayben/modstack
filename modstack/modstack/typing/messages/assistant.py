from typing import Literal

from modstack.typing.messages import ChatMessage, ChatMessageChunk, ChatRole

class AssistantMessage(ChatMessage):
    role: Literal[ChatRole.ASSISTANT]

    def __init__(
        self,
        content: str,
        name: str | None = None,
        **kwargs
    ):
        super().__init__(content, ChatRole.ASSISTANT, name=name, **kwargs)

class AssistantMessageChunk(AssistantMessage, ChatMessageChunk):
    pass