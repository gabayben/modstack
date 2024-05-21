from abc import ABC
from typing import Any, Generic, Optional, TypeVar, override

from docarray.utils._internal.misc import ProtocolType
from pydantic import Field

from modstack.typing import Artifact, AudioBytes, AudioUrl, BaseUrl, ImageBytes, ImageUrl, VideoBytes, VideoUrl

_Url = TypeVar('_Url', bound=BaseUrl)
_Bytes = TypeVar('_Bytes', bound=bytes)

class BlobArtifact(Artifact, ABC):
    base64: Optional[str] = Field(default=None, kw_only=True)

    @override
    def to_base64(
        self,
        protocol: ProtocolType = 'protobuf',
        compress: Optional[str] = None
    ) -> str:
        return self.base64 or super().to_base64(protocol=protocol, compress=compress)

class MediaArtifact(BlobArtifact, Generic[_Url, _Bytes]):
    url: _Url = Field(default=None, kw_only=True)
    bytes_: _Bytes = Field(default=None, kw_only=True)

    @override
    def to_base64(self, **kwargs) -> str:
        return super().to_base64(**kwargs)

class ImageArtifact(MediaArtifact[ImageUrl, ImageBytes]):
    pass

class AudioArtifact(MediaArtifact[AudioUrl, AudioBytes]):
    frame_rate: int | None = Field(default=None, kw_only=True)

    def __init__(
        self,
        metadata: dict[str, Any] | None = None,
        frame_rate: int | None = None,
        **kwargs
    ):
        metadata = metadata or {}
        frame_rate = frame_rate or metadata.pop('frame_rate', None)
        super().__init__(metadata=metadata, frame_rate=frame_rate, **kwargs)

class VideoArtifact(MediaArtifact[VideoUrl, VideoBytes]):
    audio: AudioArtifact | None = Field(default=None, kw_only=True)