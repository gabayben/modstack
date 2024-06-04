from typing import Literal

from modstack.artifacts.messages import ChatMessage, ChatMessageChunk, ChatRole

class UserMessage(ChatMessage):
    role: Literal[ChatRole.USER]

    def __init__(
        self,
        content: str,
        name: str | None = None,
        **kwargs
    ):
        _ = kwargs.pop('role', None)
        super().__init__(content, ChatRole.USER, name=name, **kwargs)

class UserMessageChunk(UserMessage, ChatMessageChunk):
    pass