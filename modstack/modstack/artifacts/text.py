from typing import Any, Self

from modstack.artifacts import Utf8Artifact

class TextArtifact(Utf8Artifact):
    content: str

    @property
    def content_keys(self) -> set[str]:
        return {'content'}

    def __init__(self, content: str, **kwargs):
        super().__init__(**kwargs, content=content)

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        **kwargs
    ) -> Self:
        return cls(data.decode('utf8'))

    def to_base64(self, **kwargs) -> str:
        return str(self)

    def to_utf8(self) -> str:
        return self.content

    def set_content(self, content: Any, *args) -> None:
        self.content = str(content)