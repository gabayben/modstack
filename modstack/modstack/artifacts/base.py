from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum, auto
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, Optional, Self, Union, override

from docarray.base_doc.doc import IncEx
from pydantic import Field

from modstack.typing import BaseDoc, BaseUrl, Embedding, PydanticRegistry, Serializable
from modstack.utils.constants import SCHEMA_TYPE
from modstack.utils.paths import get_mime_type
from modstack.utils.string import type_name

class Modality(StrEnum):
    TEXT = 'text'
    IMAGE = 'image'
    AUDIO = 'audio'
    VIDEO = 'video'
    MESH_3D = 'mesh_3d'
    POINT_CLOUD_3D = 'point_cloud_3d'
    MULTI_MODAL = 'multi_modal'
    BYTE_STREAM = 'byte_stream'

class ArtifactRelationship(StrEnum):
    REF = auto()
    PREVIOUS = auto()
    NEXT = auto()
    PARENT = auto()
    CHILDREN = auto()

class ArtifactInfo(Serializable):
    id: str
    type: str
    hash: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

RelatedArtifact = Union[ArtifactInfo, list[ArtifactInfo]]

class ArtifactHierarchy(dict[ArtifactRelationship, RelatedArtifact]):
    @property
    def ref(self) -> Optional[ArtifactInfo]:
        if ArtifactRelationship.REF not in self:
            return None
        related = self[ArtifactRelationship.REF]
        if not isinstance(related, ArtifactInfo):
            raise ValueError('Ref object must be a single ArtifactInfo object.')
        return related

    @property
    def previous(self) -> Optional[ArtifactInfo]:
        if ArtifactRelationship.PREVIOUS not in self:
            return None
        related = self[ArtifactRelationship.PREVIOUS]
        if not isinstance(related, ArtifactInfo):
            raise ValueError('Previous object must be a single ArtifactInfo object.')
        return related

    @property
    def next(self) -> Optional[ArtifactInfo]:
        if ArtifactRelationship.NEXT not in self:
            return None
        related = self[ArtifactRelationship.NEXT]
        if not isinstance(related, ArtifactInfo):
            raise ValueError('Next object must be a single ArtifactInfo object.')
        return related

    @property
    def parent(self) -> Optional[ArtifactInfo]:
        if ArtifactRelationship.PARENT not in self:
            return None
        related = self[ArtifactRelationship.PARENT]
        if not isinstance(related, ArtifactInfo):
            raise ValueError('Parent object must be a single ArtifactInfo object.')
        return related

    @property
    def children(self) -> Optional[list[ArtifactInfo]]:
        if ArtifactRelationship.CHILDREN not in self:
            return None
        children = self[ArtifactRelationship.CHILDREN]
        if not isinstance(children, list):
            raise ValueError('Children objects must be a list of ArtifactInfo objects.')
        return children

class Artifact(BaseDoc, ABC):
    name: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[Embedding] = Field(default=None, exclude=True, kw_only=True)
    score: Optional[float] = Field(default=None, kw_only=True)
    relationships: ArtifactHierarchy = Field(default_factory=ArtifactHierarchy)

    @property
    @abstractmethod
    def content_keys(self) -> set[str]:
        pass

    @property
    def ref(self) -> Optional[ArtifactInfo]:
        return self.relationships.ref

    @property
    def previous(self) -> Optional[ArtifactInfo]:
        return self.relationships.previous

    @property
    def next(self) -> Optional[ArtifactInfo]:
        return self.relationships.next

    @property
    def parent(self) -> Optional[ArtifactInfo]:
        return self.relationships.parent

    @property
    def children(self) -> Optional[list[ArtifactInfo]]:
        return self.relationships.children

    @classmethod
    @abstractmethod
    def modality(cls) -> str:
        pass

    @classmethod
    def from_source(cls, source: 'ArtifactSource', metadata: dict[str, Any] = {}) -> Self:
        if isinstance(source, Artifact):
            metadata['mime_type'] = metadata.get('mime_type', None)
            return cls.from_artifact(source, metadata)
        return cls.from_path(source, metadata)

    @classmethod
    def from_artifact(cls, other: 'Artifact', metadata: dict[str, Any] = {}) -> Self:
        artifact = cls.from_bytes(bytes(other))
        artifact.metadata.update({**other.metadata, **metadata})
        return artifact

    @classmethod
    def from_path(cls, path: str | Path, metadata: dict[str, Any] = {}) -> Self:
        if isinstance(path, Path):
            valid_path = path.as_uri()
        else:
            valid_path = path
        return cls.from_bytes(BaseUrl(valid_path).load_bytes())

    @override
    def model_dump(
        self,
        *,
        mode: Union[Literal['json', 'python'], str] = 'python',
        include: IncEx = None,
        exclude: IncEx = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> dict[str, Any]:
        return {
            **super().model_dump(
                mode=mode,
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
                round_trip=round_trip,
                warnings=warnings
            ),
            SCHEMA_TYPE: type_name(self.__class__)
        }

    def as_info(self) -> ArtifactInfo:
        return ArtifactInfo(
            id=self.id,
            type=self.modality(),
            hash=self.hash,
            metadata=self.metadata
        )

    @abstractmethod
    def set_content(self, *args) -> None:
        pass

    @abstractmethod
    def get_hash(self) -> str:
        pass

    def is_empty(self) -> bool:
        return bytes(self) == b''

    def pretty_repr(self, **kwargs) -> str:
        return repr(self)

    @staticmethod
    def get_mime_type(source: 'ArtifactSource') -> str:
        path: Path
        if isinstance(source, str):
            path = Path(source)
        if isinstance(source, Path):
            mime_type = get_mime_type(source)
        elif isinstance(source, BaseUrl):
            mime_type = source.mime_type
        elif isinstance(source, Artifact):
            mime_type = source.metadata.get('mime_type', None)
        else:
            raise ValueError(f'Unsupported data source type: {type(source).__name__}.')
        return mime_type

    class Config:
        extra = 'allow'
        arbitrary_types_allowed = True

StrictArtifactSource = Path | Artifact
ArtifactSource = str | StrictArtifactSource

class Utf8Artifact(Artifact, ABC):
    @classmethod
    def modality(cls) -> str:
        return Modality.TEXT

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return str(self) == other
        return super().__eq__(other)

    def __str__(self) -> str:
        return self.to_utf8()

    def __contains__(self, item: Any) -> bool:
        text = item if isinstance(item, str) else str(item)
        return str(self).__contains__(text)

    @abstractmethod
    def to_utf8(self) -> str:
        pass
    
    def get_hash(self) -> str:
        identity = self.to_utf8() + str(self.metadata)
        return sha256(identity.encode('utf8', 'surrogatepass')).hexdigest()

    def to_bytes(self, **kwargs) -> bytes:
        return str(self).encode(encoding='utf8')

    def _get_string_for_regex_filter(self) -> str:
        return str(self)

@dataclass
class ArtifactQuery:
    value: Artifact
    metadata: dict[str, Any] = field(default_factory=dict)

class _ArtifactRegistry(PydanticRegistry[Artifact]):
    pass

artifact_registry = _ArtifactRegistry()