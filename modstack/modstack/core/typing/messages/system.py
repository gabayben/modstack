from typing import Literal

from modstack.core.typing.messages import ChatMessage, ChatMessageChunk, ChatRole

class SystemMessage(ChatMessage):
    role: Literal[ChatRole.SYSTEM]

    def __init__(
        self,
        content: str,
        name: str | None = None,
        **kwargs
    ):
        super().__init__(content, ChatRole.SYSTEM, name=name, **kwargs)

class SystemMessageChunk(SystemMessage, ChatMessageChunk):
    pass