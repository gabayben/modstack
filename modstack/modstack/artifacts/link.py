from typing import Any

from modstack.artifacts import ArtifactType, TextArtifact, Utf8Artifact
from modstack.typing import TextUrl
from modstack.utils.string import mapping_to_str

class LinkArtifact(Utf8Artifact):
    link: TextUrl
    title: str
    position: int | None = None
    description: str | None = None

    def __init__(
        self,
        link: str,
        title: str,
        position: int | None = None,
        description: str | None = None,
        metadata: dict[str, Any] = {},
        **kwargs
    ):
        super().__init__(
            link=TextUrl(link), # type: ignore[call-args]
            title=title,
            position=position,
            description=description,
            metadata=metadata,
            **kwargs
        )

    @classmethod
    def artifact_type(cls) -> str:
        return ArtifactType.LINK

    def to_bytes(self, **kwargs) -> bytes:
        return self.link.load_bytes()

    def to_utf8(self) -> str:
        return mapping_to_str(dict(self))

    def to_text_artifact(self) -> TextArtifact:
        return TextArtifact(
            self.link.load(),
            **self.model_dump(exclude={'link', 'title', 'position', 'description', 'metadata'}),
            metadata={
                'link': str(self.link),
                'title': self.title,
                'position': self.position,
                'description': self.description,
                **self.metadata
            }
        )