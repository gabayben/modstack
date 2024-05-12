from typing import Any

from modstack.typing import Artifact, TextArtifact, TextUrl
from modstack.utils.display import mapping_to_str

class LinkArtifact(Artifact):
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

    def __str__(self) -> str:
        return self.link.load()

    def to_bytes(self, **kwargs) -> bytes:
        return self.link.load_bytes()

    def to_text_artifact(self) -> TextArtifact:
        return TextArtifact(
            mapping_to_str(dict(self)),
            id=self.id,
            metadata=self.metadata
        )