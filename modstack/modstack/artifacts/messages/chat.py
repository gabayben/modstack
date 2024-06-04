from enum import StrEnum
from typing import Any, Literal, Self

from modstack.artifacts.messages import MessageArtifact, MessageChunk

class ChatRole(StrEnum):
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'
    FUNCTION = 'function'

class ChatMessage(MessageArtifact):
    message_type: Literal['chat']
    role: ChatRole | str

    def __init__(
        self,
        content: str,
        role: str,
        name: str | None = None,
        **kwargs
    ):
        _ = kwargs.pop('message_type', None)
        super().__init__(content, 'chat', role=role, name=name, **kwargs)

    @classmethod
    def from_user(cls, content: str, **kwargs) -> Self:
        return cls(content, ChatRole.USER, **kwargs)

    @classmethod
    def from_assistant(cls, content: str, metadata: dict[str, Any] = {}, **kwargs):
        return cls(content, ChatRole.ASSISTANT, metadata=metadata, **kwargs)

    @classmethod
    def from_system(cls, content: str, **kwargs) -> Self:
        return cls(content, ChatRole.SYSTEM, **kwargs)

    @classmethod
    def from_function(cls, content: str, name: str, **kwargs) -> Self:
        return cls(content, ChatRole.FUNCTION, name=name, **kwargs)

    def to_utf8(self) -> str:
        if not self.role:
            return self.content
        text = self.role
        if self.name:
            text += f' {self.name}'
        return f'{text}:\n{self.content}'

    def to_common_format(self) -> dict[str, str]:
        msg = {'content': self.content, 'role': self.role}
        if self.name:
            msg['name'] = self.name
        return msg

class ChatMessageChunk(MessageChunk, ChatMessage):
    message_type: Literal['chat_chunk']

    def __init__(
        self,
        content: str,
        role: str,
        name: str | None = None,
        **kwargs
    ):
        _ = kwargs.pop('message_type', None)
        super().__init__(
            content,
            'chat_chunk',
            role=role,
            name=name,
            **kwargs
        )