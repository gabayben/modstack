from typing import Any

from pydantic import Field

from modstack.contracts import Contract
from modstack.typing import Serializable, Utf8Artifact

class EmbedTextResponse(Serializable):
    artifacts: list[Utf8Artifact]
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __init__(
        self,
        artifacts: list[Utf8Artifact],
        metadata: dict[str, Any] ={},
        **kwargs
    ):
        super().__init__(artifacts=artifacts, metadata=metadata, **kwargs)

class EmbedText(Contract):
    artifacts: list[Utf8Artifact]

    def __init__(self, artifacts: list[Utf8Artifact], **kwargs):
        super().__init__(artifacts=artifacts, **kwargs)