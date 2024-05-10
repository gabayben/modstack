from abc import ABC
from typing import Generic, Optional, TypeVar, override

from docarray.utils._internal.misc import ProtocolType
from pydantic import Field

from modstack.typing import Artifact, AudioBytes, AudioUrl, BaseBytes, BaseUrl, ImageBytes, ImageUrl, VideoBytes, VideoUrl

_Url = TypeVar('_Url', bound=BaseUrl)
_Bytes = TypeVar('_Bytes', bound=BaseBytes)

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

class VideoArtifact(MediaArtifact[VideoUrl, VideoBytes]):
    pass

class AudioArtifact(MediaArtifact[AudioUrl, AudioBytes]):
    pass