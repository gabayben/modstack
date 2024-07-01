from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, Optional, Self, TYPE_CHECKING, TypedDict, Union, override

from docarray.base_doc.doc import IncEx
from pydantic import Field

from modstack.typing import BaseDoc, BaseUrl, CoordinateSystem, ModelDict, Embedding, Points, PydanticRegistry
from modstack.utils.constants import SCHEMA_TYPE
from modstack.utils.paths import get_mime_type
from modstack.utils.string import type_name

if TYPE_CHECKING:
    from modstack.artifacts.link import Link

class ArtifactType(StrEnum):
    TEXT = 'Text'
    FORMULA = 'Formula'
    COMPOSITE_TEXT = 'CompositeText'
    FIGURE_CAPTION = 'FigureCaption'
    NARRATIVE_TEXT = 'NarrativeText'
    LIST_ITEM = 'ListItem'
    TITLE = 'Title'
    ADDRESS = 'Address'
    EMAIL_ADDRESS = 'EmailAddress'
    EMAIL_SENDER = 'EmailSender'
    EMAIL_RECIPIENT = 'EmailRecipient'
    EMAIL_SUBJECT = 'EmailSubject'
    BODY_TEXT = 'BodyText'
    EMAIL_METADATA = 'EmailMetadata'
    RECEIVED_INFO = 'ReceivedInfo',
    EMAIL_ATTACHMENT = 'EmailAttachment'
    LINK = 'Link'
    CHECKBOX = 'Checkbox'
    IMAGE = 'Image'

class DataSourceMetadata(TypedDict, total=False):
    """
    Metadata fields that pertain to the data source of the document.
    """

    url: Optional[str]
    version: Optional[str]
    date_created: Optional[str]
    date_modified: Optional[str]
    date_processed: Optional[str]
    record_locator: Optional[dict[str, Any]]
    permissions_data: Optional[list[dict[str, Any]]]

class CoordinatesMetadata(TypedDict, total=False):
    """
    Metadata fields that pertain to the coordinates of the artifact.
    """

    points: Optional[Points]
    system: Optional[CoordinateSystem]

class RegexMetadata(TypedDict):
    """
    Metadata that is extracted from a document artifact via regex.
    """

    text: str
    start: int
    end: int

class ArtifactMetadata(ModelDict):
    parent_id: Optional[str]
    datestamp: Optional[datetime]
    filename: Optional[str]
    filetype: Optional[str]
    url: Optional[str]
    mime_type: Optional[str]
    page_name: Optional[str]
    page_number: Optional[int]
    detection_origin: Optional[str]
    detection_class_prob: Optional[float]
    emphasized_text_contents: Optional[list[str]]
    emphasized_text_tags: Optional[list[str]]
    signature: Optional[str]
    languages: Optional[list[str]]
    is_continuation: Optional[bool]
    links: Optional[list['Link']]
    source: Optional[DataSourceMetadata]
    coordinates: Optional[CoordinatesMetadata]
    regex: Optional[RegexMetadata]

class Artifact(BaseDoc, ABC):
    name: Optional[str] = None
    metadata: ArtifactMetadata = Field(default_factory=ArtifactMetadata)
    embedding: Optional[Embedding] = Field(default=None, exclude=True, kw_only=True)
    score: Optional[float] = Field(default=None, exclude=True, kw_only=True)

    @property
    @abstractmethod
    def category(self) -> str:
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

    def store_model_dump(self, exclude: set[str] = {}, **kwargs) -> dict[str, Any]:
        return {
            **self.model_dump(
                **kwargs,
                exclude={*exclude, 'embedding', 'score', 'metadata'}
            ),
            **self.metadata
        }

    @abstractmethod
    def get_hash(self) -> str:
        pass

    def is_empty(self) -> bool:
        return bytes(self) == b''

    def pretty_repr(self, **kwargs) -> str:
        return repr(self)

    @abstractmethod
    def set_content(self, content: Union[str, bytes]) -> None:
        pass

    @staticmethod
    def get_mime_type(source: 'ArtifactSource') -> str:
        path: Path
        if isinstance(source, str):
            path = Path(source)
        if isinstance(source, Path):
            mime_type = get_mime_type(source)
        elif isinstance(source, BaseUrl):
            mime_type = source.mime_type()
        elif isinstance(source, Artifact):
            mime_type = source.metadata.mime_type
        else:
            raise ValueError(f'Unsupported data source type: {type(source).__name__}.')
        return mime_type

    class Config:
        extra = 'allow'
        arbitrary_types_allowed = True

StrictArtifactSource = Path | Artifact
ArtifactSource = str | StrictArtifactSource

class Utf8Artifact(Artifact, ABC):
    def __str__(self) -> str:
        return self.to_utf8()

    def __contains__(self, item: Any) -> bool:
        text = item if isinstance(item, str) else str(item)
        return str(self).__contains__(text)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return (
            str(self) == str(other)
            and self.embedding == other.embedding
            and self.metadata.coordinates == other.metadata.coordinates
        )

    @abstractmethod
    def to_utf8(self) -> str:
        pass

    def to_base64(self, **kwargs) -> str:
        return str(self)

    def to_bytes(self, **kwargs) -> bytes:
        return str(self).encode(encoding='utf-8')

    def get_hash(self) -> str:
        identity = self.to_utf8() + str(self.metadata)
        return sha256(identity.encode('utf-8', 'surrogatepass')).hexdigest()

    def _get_string_for_regex_filter(self) -> str:
        return str(self)

@dataclass
class ArtifactQuery:
    value: Artifact
    metadata: dict[str, Any] = field(default_factory=dict)

class _ArtifactRegistry(PydanticRegistry[Artifact]):
    pass

artifact_registry = _ArtifactRegistry()