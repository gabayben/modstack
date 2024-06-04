from typing import Self

from modstack.artifacts import Utf8Artifact

class TextArtifact(Utf8Artifact):
    content: str

    def __init__(self, content: str, **kwargs):
        super().__init__(**kwargs, content=content)

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        **kwargs
    ) -> Self:
        return cls(data.decode('utf-8'))

    def __str__(self) -> str:
        return self.content

    def to_base64(self, **kwargs) -> str:
        return str(self)

    def to_utf8(self) -> str:
        return str(self)