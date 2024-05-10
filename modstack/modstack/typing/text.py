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

    def to_bytes(self, **kwargs) -> bytes:
        return str(self).encode(encoding=self.encoding)