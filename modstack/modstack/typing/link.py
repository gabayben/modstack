from typing import Any

from modstack.typing import TextArtifact, TextUrl, Utf8Artifact
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

    def to_bytes(self, **kwargs) -> bytes:
        return self.link.load_bytes()

    def __str__(self) -> str:
        return self.link.load(charset='utf-8')

    def to_utf8(self) -> str:
        return str(self)

    def to_text_artifact(self) -> TextArtifact:
        return TextArtifact(
            mapping_to_str(dict(self)),
            id=self.id,
            metadata=self.metadata
        )