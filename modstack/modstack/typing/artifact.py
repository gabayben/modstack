from abc import ABC
from pathlib import Path
from typing import Any, Optional, Self

from pydantic import Field

from modstack.typing import BaseDoc, BaseUrl, Embedding, TextUrl

class Artifact(BaseDoc, ABC):
    name: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[Embedding] = Field(default=None, exclude=True, kw_only=True)
    score: Optional[float] = Field(default=None, kw_only=True)

    @classmethod
    def from_source(cls, source: 'ArtifactSource', metadata: dict[str, Any] = {}) -> Self:
        if isinstance(source, Artifact):
            return cls.from_artifact(source, metadata)
        elif isinstance(source, BaseUrl):
            return cls.from_url(source, metadata)
        return cls.from_path(source, metadata)

    @classmethod
    def from_artifact(cls, other: 'Artifact', metadata: dict[str, Any] = {}) -> Self:
        artifact = cls.from_bytes(bytes(other))
        artifact.metadata.update({**other.metadata, **metadata})
        return artifact

    @classmethod
    def from_url(cls, url: BaseUrl, metadata: dict[str, Any] = {}) -> Self:
        artifact = cls.from_bytes(url.load_bytes())
        artifact.metadata.update(metadata)
        artifact.metadata['url'] = url
        return artifact

    @classmethod
    def from_path(cls, path: str | Path, metadata: dict[str, Any] = {}) -> Self:
        if isinstance(path, Path):
            valid_path = path.as_uri()
        else:
            valid_path = path
        return cls.from_url(TextUrl(valid_path), metadata) # type: ignore[call-args]

    def to_utf8(self) -> str:
        return bytes(self).decode('utf-8')

    def is_empty(self) -> bool:
        return bytes(self) == b''

    class Config:
        extra = 'allow'
        arbitrary_types_allowed = True

ArtifactSource = str | Path | BaseUrl | Artifact