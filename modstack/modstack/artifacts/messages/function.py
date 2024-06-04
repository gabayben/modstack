from typing import Literal

from modstack.artifacts.messages import ChatMessage, ChatMessageChunk, ChatRole

class FunctionMessage(ChatMessage):
    role: Literal[ChatRole.FUNCTION]

    def __init__(
        self,
        content: str,
        name: str | None = None,
        **kwargs
    ):
        super().__init__(content, ChatRole.FUNCTION, name=name, **kwargs)

class FunctionMessageChunk(FunctionMessage, ChatMessageChunk):
    pass