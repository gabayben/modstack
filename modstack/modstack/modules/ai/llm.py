from typing import Iterable

from modstack.typing import Schema
from modstack.artifacts.messages import MessageArtifact

class LLMRequest(Schema):
    prompt: str
    history: Iterable[MessageArtifact] | None = None

    def __init__(
        self,
        prompt: str,
        history: Iterable[MessageArtifact] | None = None,
        **kwargs
    ):
        super().__init__(
            prompt=prompt,
            history=history,
            **kwargs
        )