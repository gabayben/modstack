from modstack.artifacts import ArtifactMetadata, ArtifactType, Utf8Artifact

class Checkbox(Utf8Artifact):
    checked: bool = False

    @property
    def category(self) -> str:
        return ArtifactType.CHECKBOX

    @property
    def _content_keys(self) -> set[str]:
        return {'checked'}

    def __init__(
        self,
        checked: bool = False,
        metadata: ArtifactMetadata = ArtifactMetadata(),
        **kwargs
    ):
        super().__init__(
            checked=checked,
            metadata=metadata,
            **kwargs
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Checkbox):
            return False
        return (
            self.metadata.coordinates == other.metadata.coordinates
            and self.checked == other.checked
        )

    def set_content(self, checked: str = 'False') -> None:
        self.checked = bool(checked)

    def to_utf8(self) -> str:
        return str(self.checked)