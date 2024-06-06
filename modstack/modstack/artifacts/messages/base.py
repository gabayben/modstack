from typing import Any, Optional, Union

from modstack.artifacts import Utf8Artifact
from modstack.artifacts.messages.utils import merge_content

class MessageArtifact(Utf8Artifact):
    content: str
    message_type: str
    name: Optional[str] = None
    
    def __init__(
        self, 
        content: str,
        message_type: str,
        name: Optional[str] = None,
        metadata: dict[str, Any] = {},
        **kwargs
    ):
        super().__init__(
            content=content,
            message_type=message_type,
            name=name,
            metadata=metadata,
            **kwargs
        )
    
    def to_utf8(self) -> str:
        return self.content

class MessageChunk(MessageArtifact):
    def __add__(self, other: Union[str, list[str], 'MessageChunk']) -> 'MessageChunk':
        if isinstance(other, MessageChunk):
            return self.__class__(
                content=merge_content(self.content, other.content),
                message_type=self.message_type,
                name=self.name,
                metadata={**self.metadata, **other.metadata}
            )
        return self.__class__(
            content=merge_content(
                self.content,
                other if isinstance(other, str) else '\n'.join(other)
            ),
            message_type=self.message_type,
            name=self.name,
            metadata=self.metadata
        )