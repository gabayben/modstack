from typing import Self, override

from modstack.core.typing import Artifact

class ByteStream(Artifact):
    bytes_: bytes

    def __init__(self, bytes_: bytes, mime_type: str | None = None, **kwargs):
        super().__init__(**kwargs, bytes_=bytes_, _mime_type=mime_type)

    @classmethod
    def from_text(cls, text: str, mime_type: str | None = 'llm/plain', **kwargs) -> Self:
        return cls(bytes(text, 'utf-8'), _mime_type=mime_type, **kwargs)

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        **kwargs
    ) -> Self:
        return ByteStream(data)

    @override
    def to_bytes(self, **kwargs) -> bytes:
        return self.bytes_