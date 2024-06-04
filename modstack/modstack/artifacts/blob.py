from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, TypeVar, override

from docarray.typing import Mesh3DUrl
from docarray.utils._internal.misc import ProtocolType
from pydantic import Field

from modstack.artifacts import Artifact, ArtifactType
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
    def link(self) -> BaseUrl:
        pass

    def to_bytes(
        self,
        protocol: ProtocolType = 'protobuf',
        compress: Optional[str] = None
    ) -> bytes:
        if self.link:
            return self.link.load_bytes()
        super().to_bytes(protocol=protocol, compress=compress)

    @override
    def to_base64(
        self,
        protocol: ProtocolType = 'protobuf',
        compress: Optional[str] = None
    ) -> str:
        return self.base64 or super().to_base64(protocol=protocol, compress=compress)

class MediaArtifact(BlobArtifact, Generic[_Url, _Bytes], ABC):
    url: _Url = Field(default=None, kw_only=True)
    bytes_: _Bytes = Field(default=None, kw_only=True)

    @property
    def link(self) -> _Url:
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

class ImageArtifact(MediaArtifact[ImageUrl, ImageBytes]):
    tensor: ImageTenser | None = Field(default=None, kw_only=True)

    @classmethod
    def artifact_type(cls) -> str:
        return ArtifactType.IMAGE

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
    def artifact_type(cls) -> str:
        return ArtifactType.AUDIO

class VideoArtifact(MediaArtifact[VideoUrl, VideoBytes]):
    tensor: VideoTensor | None = Field(default=None, kw_only=True)
    key_frame_indices: BaseTensor | None = Field(default=None, kw_only=True)
    audio: AudioArtifact | None = Field(default=None, kw_only=True)

    @classmethod
    def artifact_type(cls) -> str:
        return ArtifactType.VIDEO

class Mesh3D(MediaArtifact[Mesh3DUrl, bytes]):
    tensor: VerticesAndFaces | None = Field(default=None, kw_only=True)

    @classmethod
    def artifact_type(cls) -> str:
        return ArtifactType.MESH_3D

class PointCloud3D(MediaArtifact[PointCloud3DUrl, bytes]):
    tensor: PointsAndColors | None = Field(default=None, kw_only=True)

    @classmethod
    def artifact_type(cls) -> str:
        return ArtifactType.POINT_CLOUD_3D