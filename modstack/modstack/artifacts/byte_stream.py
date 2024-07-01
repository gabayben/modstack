from hashlib import sha256
from typing import Any, Self, override

from modstack.artifacts import Artifact

class ByteStream(Artifact):
    bytes_: bytes

    @property
    def _content_keys(self) -> set[str]:
        return {'bytes_'}

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

    def set_content(self, content: Any, *args) -> None:
        if isinstance(content, str):
            self.bytes_ = bytes(content, 'utf-8')
        else:
            self.bytes_ = bytes(content)

    def get_hash(self) -> str:
        return sha256(bytes(self)).hexdigest()