from abc import ABC, abstractmethod
import base64
from hashlib import sha256
from typing import Any, Generic, Optional, TypeVar, Union, override

from docarray.typing import Mesh3DUrl
from docarray.utils._internal.misc import ProtocolType
from pydantic import Field

from modstack.artifacts import Artifact, Modality
from modstack.typing import (
    AudioBytes,
    AudioTensor,
    AudioUrl,
    BaseTensor,
    BaseUrl,
    ImageBytes,
    ImageTenser,
    ImageUrl,
    PointCloud3DUrl,
    PointsAndColors,
    VerticesAndFaces,
    VideoBytes,
    VideoTensor,
    VideoUrl
)

_Url = TypeVar('_Url', bound=BaseUrl)
_Bytes = TypeVar('_Bytes', bound=bytes)

class BlobArtifact(Artifact, ABC):
    base64: Optional[str] = Field(default=None, kw_only=True)

    @property
    @abstractmethod
    def link(self) -> Optional[BaseUrl]:
        pass

    def to_bytes(
        self,
        protocol: ProtocolType = 'protobuf',
        compress: Optional[str] = None
    ) -> bytes:
        if self.base64 is not None:
            return base64.b64decode(self.base64)
        if self.link:
            return self.link.load_bytes()
        return super().to_bytes(protocol=protocol, compress=compress)

    @override
    def to_base64(
        self,
        protocol: ProtocolType = 'protobuf',
        compress: Optional[str] = None
    ) -> str:
        return self.base64 or super().to_base64(protocol=protocol, compress=compress)

    def get_hash(self) -> str:
        return sha256(bytes(self)).hexdigest()

class MediaArtifact(BlobArtifact, Generic[_Url, _Bytes], ABC):
    url: Optional[_Url] = Field(default=None, kw_only=True)
    bytes_: Optional[_Bytes] = Field(default=None, kw_only=True)

    @property
    def content_keys(self) -> set[str]:
        return {'url', 'bytes_'}

    @property
    def link(self) -> Optional[_Url]:
        return self.url

    @override
    def to_bytes(
        self,
        protocol: ProtocolType = 'protobuf',
        compress: Optional[str] = None
    ) -> bytes:
        if self.bytes_:
            return self.bytes_
        return super().to_bytes(protocol=protocol, compress=compress)

    def set_content(self, content: Union[str, bytes], *args) -> None:
        pass

class ImageArtifact(MediaArtifact[ImageUrl, ImageBytes]):
    tensor: ImageTenser | None = Field(default=None, kw_only=True)

    @classmethod
    def modality(cls) -> str:
        return Modality.IMAGE

class AudioArtifact(MediaArtifact[AudioUrl, AudioBytes]):
    tensor: AudioTensor | None = Field(default=None, kw_only=True)
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

    @classmethod
    def modality(cls) -> str:
        return Modality.AUDIO

class VideoArtifact(MediaArtifact[VideoUrl, VideoBytes]):
    tensor: VideoTensor | None = Field(default=None, kw_only=True)
    key_frame_indices: BaseTensor | None = Field(default=None, kw_only=True)
    audio: AudioArtifact | None = Field(default=None, kw_only=True)

    @classmethod
    def modality(cls) -> str:
        return Modality.VIDEO

class Mesh3D(MediaArtifact[Mesh3DUrl, bytes]):
    tensor: VerticesAndFaces | None = Field(default=None, kw_only=True)

    @classmethod
    def modality(cls) -> str:
        return Modality.MESH_3D

class PointCloud3D(MediaArtifact[PointCloud3DUrl, bytes]):
    tensor: PointsAndColors | None = Field(default=None, kw_only=True)

    @classmethod
    def modality(cls) -> str:
        return Modality.POINT_CLOUD_3D