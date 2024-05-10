from typing import Self, override

from modstack.typing import Artifact

class ByteStream(Artifact):
    bytes_: bytes
    content_type: str

    def __init__(self, bytes_: bytes, content_type: str = '', **kwargs):
        super().__init__(**kwargs, bytes_=bytes_, content_type=content_type)

    @classmethod
    def from_text(cls, text: str, content_type: str = '') -> Self:
        return cls(bytes(text, 'utf-8'), content_type=content_type)

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