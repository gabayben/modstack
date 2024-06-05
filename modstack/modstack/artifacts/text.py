from typing import Self

from modstack.artifacts import ArtifactType, Utf8Artifact

class TextArtifact(Utf8Artifact):
    content: str

    def __init__(self, content: str, **kwargs):
        super().__init__(**kwargs, content=content)

    @classmethod
    def artifact_type(cls) -> str:
        return ArtifactType.TEXT

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