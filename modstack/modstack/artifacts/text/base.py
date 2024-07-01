from abc import ABC
from typing import Any, Self, Union, override

from modstack.artifacts import Artifact, ArtifactMetadata, ArtifactType, Utf8Artifact

class TextBase(Utf8Artifact, ABC):
    content: str

    def __init__(
        self,
        content: str,
        metadata: ArtifactMetadata = ArtifactMetadata(),
        **kwargs
    ):
        super().__init__(
            content=content,
            metadata=metadata,
            **kwargs
        )

    @classmethod
    def from_bytes(cls, data: bytes, **kwargs) -> Self:
        return cls(data.decode('utf-8'))

    @override
    def store_model_dump(self, **kwargs) -> dict[str, Any]:
        return super().store_model_dump(exclude={'content'}, **kwargs)

    def to_utf8(self) -> str:
        return self.content

    def set_content(self, content: Union[str, bytes]) -> None:
        if isinstance(content, str):
            self.content = content
        else:
            self.content = content.decode('utf-8')

class Text(TextBase):
    """Artifact for capturing free text from within document."""

    @property
    def category(self) -> str:
        return ArtifactType.TEXT

class Formula(TextBase):
    """An artifact containing formulas in a document."""

    @property
    def category(self) -> str:
        return ArtifactType.FORMULA

class CompositeText(TextBase):
    """
    A chunk formed from text (non-Table) artifacts.

    Only produced by chunking. An instance may be formed by combining one or more sequential
    artifacts produced by partitioning. It it also used when text-splitting an "oversized" artifact,
    a single artifact that by itself is larger than the requested chunk size.
    """

    @property
    def category(self) -> str:
        return ArtifactType.COMPOSITE_TEXT

class FigureCaption(TextBase):
    """An artifact for capturing text associated with figure captions."""

    @property
    def category(self) -> str:
        return ArtifactType.FIGURE_CAPTION

class NarrativeText(TextBase):
    """
    NarrativeText is an artifact consisting of multiple, well-formulated sentences.
    This excludes artifacts such as titles, headers, footers, and captions.
    """

    @property
    def category(self) -> str:
        return ArtifactType.NARRATIVE_TEXT

    def __init__(
        self,
        sentences: list[Union[str, Artifact]],
        metadata: ArtifactMetadata = ArtifactMetadata(),
        **kwargs
    ):
        super().__init__(
            content=' '.join([str(s) for s in sentences]),
            metadata=metadata,
            **kwargs
        )

class ListItem(Text):
    """ListItem is a NarrativeText artifact that is part of a list."""

    @property
    def category(self) -> str:
        return ArtifactType.LIST_ITEM

class Title(Text):
    """A text artifact for capturing titles."""

    @property
    def category(self) -> str:
        return ArtifactType.TITLE

class Address(Text):
    """A text artifact for capturing addresses."""

    @property
    def category(self) -> str:
        return ArtifactType.ADDRESS