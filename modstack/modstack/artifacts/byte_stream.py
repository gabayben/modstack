from hashlib import sha256
from typing import Self, override

from modstack.artifacts import Artifact, Modality

class ByteStream(Artifact):
    bytes_: bytes

    def __init__(self, bytes_: bytes, mime_type: str | None = None, **kwargs):
        super().__init__(**kwargs, bytes_=bytes_, _mime_type=mime_type)

    @classmethod
    def modality(cls) -> str:
        return Modality.BYTE_STREAM

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

    def get_hash(self) -> str:
        return sha256(bytes(self)).hexdigest()