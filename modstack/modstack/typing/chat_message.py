from enum import StrEnum
from typing import Any, Self

from modstack.typing import Utf8Artifact

class ChatRole(StrEnum):
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'
    FUNCTION = 'function'

class ChatMessage(Utf8Artifact):
    content: str
    role: ChatRole | str | None = None
    name: str | None = None

    def __init__(
        self,
        content: str,
        role: str,
        name: str | None = None,
        **kwargs
    ):
        super().__init__(content=content, role=role, name=name, **kwargs)

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