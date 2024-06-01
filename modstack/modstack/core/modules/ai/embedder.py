from typing import Any

from pydantic import Field

from modstack.core.artifacts import Utf8Artifact
from modstack.core.typing import Serializable

class TextEmbeddingRequest(Serializable):
    artifacts: list[Utf8Artifact]

class TextEmbeddingResponse(Serializable):
    artifacts: list[Utf8Artifact]
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __init__(
        self,
        artifacts: list[Utf8Artifact],
        metadata: dict[str, Any] ={},
        **kwargs
    ):
        super().__init__(artifacts=artifacts, metadata=metadata, **kwargs)