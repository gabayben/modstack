from pydantic import Field

from modstack.artifacts import Utf8Artifact
from modstack.typing import Schema
from modstack.artifacts.messages import MessageArtifact

class LLMRequest(Schema):
    prompt: Utf8Artifact
    messages: list[MessageArtifact] = Field(default_factory=list)

    def __init__(
        self,
        prompt: Utf8Artifact,
        messages: list[MessageArtifact] = [],
        **kwargs
    ):
        super().__init__(
            prompt=prompt,
            messages=messages,
            **kwargs
        )