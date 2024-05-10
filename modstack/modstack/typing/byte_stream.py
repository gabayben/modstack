from typing import Self, override

from modstack.typing import Artifact

class ByteStream(Artifact):
    bytes_: bytes

    def __init__(self, bytes_: bytes, mime_type: str | None = None, **kwargs):
        super().__init__(**kwargs, bytes_=bytes_, _mime_type=mime_type)

    @classmethod
    def from_text(cls, text: str, mime_type: str | None = 'text/plain', **kwargs) -> Self:
        return cls(bytes(text, 'utf-8'), _mime_type=mime_type, **kwargs)

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        mime_type: str | None = None,
        **kwargs
    ) -> Self:
        return ByteStream(data, _mime_type=mime_type)

    @override
    def to_bytes(self, **kwargs) -> bytes:
        return self.bytes_