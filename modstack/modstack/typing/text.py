from typing import Type

from docarray.base_doc.mixins.io import T

from modstack.typing import Artifact

class TextArtifact(Artifact):
    content: str
    encoding: str = 'utf-8'

    def __init__(self, content: str, **kwargs):
        super().__init__(**kwargs, content=content)

    def __str__(self) -> str:
        return self.content

    def to_base64(self, **kwargs) -> str:
        return str(self)

    @classmethod
    def from_bytes(
        cls: Type[T],
        data: bytes,
        **kwargs
    ) -> T:
        return cls(data.decode('utf-8'))

    def to_bytes(self, **kwargs) -> bytes:
        return str(self).encode(encoding=self.encoding)