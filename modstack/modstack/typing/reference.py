from typing import Any

from modstack.typing import Artifact, TextArtifact, TextUrl

class ReferenceArtifact(Artifact):
    title: str
    link: TextUrl
    description: str | None = None

    def __init__(
        self,
        title: str,
        link: str,
        description: str | None = None,
        metadata: dict[str, Any] = {},
        **kwargs
    ):
        super().__init__(
            title=title,
            link=TextUrl(link), #type: ignore[call-args]
            description=description,
            metadata=metadata,
            **kwargs
        )

    def __str__(self) -> str:
        return self.link.load()

    def to_bytes(self, **kwargs) -> bytes:
        return self.link.load_bytes()

    def to_text_artifact(self) -> TextArtifact:
        text = (
            f'title: {self.title}' +
            f'\nlink: {str(self.link)}' +
            (f'\ndescription: {self.description}' if self.description else '')
        )
        return TextArtifact(text, metadata=self.metadata)