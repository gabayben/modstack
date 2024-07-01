from typing import Any, override

from modstack.artifacts import ArtifactMetadata, ArtifactType, Text, Utf8Artifact
from modstack.typing import TextUrl
from modstack.utils.string import mapping_to_str

class Link(Utf8Artifact):
    link: TextUrl
    title: str
    position: int | None = None
    text: str | None = None

    @property
    @override
    def category(self) -> str:
        return ArtifactType.LINK

    @property
    def _content_keys(self) -> set[str]:
        return {'link'}

    def __init__(
        self,
        link: str,
        title: str,
        position: int | None = None,
        text: str | None = None,
        metadata: dict[str, Any] = {},
        **kwargs
    ):
        super().__init__(
            link=TextUrl(link), # type: ignore[call-args]
            title=title,
            position=position,
            text=text,
            metadata=metadata,
            **kwargs
        )

    def to_bytes(self, **kwargs) -> bytes:
        return self.link.load_bytes()

    def to_utf8(self) -> str:
        return mapping_to_str(dict(self))

    def to_text_artifact(self) -> Text:
        return Text(
            self.link.load(),
            **self.model_dump(exclude={'link', 'title', 'position', 'description', 'metadata'}),
            metadata=ArtifactMetadata({
                'link': str(self.link),
                'title': self.title,
                'position': self.position,
                'description': self.text,
                **self.metadata
            })
        )

    def set_content(self, link: str, *args) -> None:
        self.link = TextUrl(link) # type: ignore[call-args]