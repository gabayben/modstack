"""
Credit to LangChain - https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/messages/base.py
"""

from enum import StrEnum
from typing import Any, Literal, Optional, Union, override

from modstack.artifacts import ArtifactType, Utf8Artifact
from modstack.artifacts.messages.utils import merge_content
from modstack.utils.merge import merge_dicts

class MessageType(StrEnum):
    HUMAN = 'user'
    AI = 'assistant'
    SYSTEM = 'system'
    FUNCTION = 'function'
    TOOL = 'tool'

class MessageArtifact(Utf8Artifact):
    content: str
    name: Optional[str] = None
    message_type: MessageType | str
    role: Optional[str] = None

    @property
    @override
    def category(self) -> str:
        return ArtifactType.MESSAGE

    @property
    def _content_keys(self) -> set[str]:
        return {'content'}

    def __init__(
        self,
        content: str,
        message_type: MessageType | str,
        role: str='',
        name: str | None = None,
        **kwargs
    ):
        _ = kwargs.pop('message_type', None)
        super().__init__(
            content=content,
            name=name,
            message_type=message_type,
            role=role,
            **kwargs
        )

    def to_utf8(self) -> str:
        if not self.message_type:
            return self.content
        text = self.message_type
        if self.name:
            text += f' {self.name}'
        return f'{text}:\n{self.content}'

    def to_common_format(self) -> dict[str, str]:
        msg = {'content': self.content, 'role': self.message_type}
        if self.name:
            msg['name'] = self.name
        return msg

    def set_content(self, content: Any) -> None:
        self.content = str(content)

    @override
    def pretty_repr(self, **kwargs) -> str:
        title = f'{self.message_type.title()} Message'
        if self.name is not None:
            title += f'\nName: {self.name}'
        return f'{title}\n\n{self.content}'

class MessageChunk(MessageArtifact):
    def __init__(
        self,
        content: str,
        message_type: MessageType,
        role: str='',
        name: str | None = None,
        **kwargs
    ):
        super().__init__(
            content,
            message_type=message_type,
            role=role,
            name=name,
            **kwargs
        )

    def __add__(self, other: Union[str, list[str], 'MessageChunk']) -> 'MessageChunk':
        if isinstance(other, MessageChunk):
            return self.__class__(
                content=merge_content(self.content, other.content),
                message_type=self.message_type,
                name=self.name,
                metadata=merge_dicts(self.metadata, other.metadata),
                role=self.role
            )
        return self.__class__(
            content=merge_content(
                self.content,
                other if isinstance(other, str) else '\n'.join(other)
            ),
            message_type=self.message_type,
            name=self.name,
            metadata=self.metadata,
            role=self.role
        )