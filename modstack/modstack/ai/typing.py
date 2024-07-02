from typing import NamedTuple, Union

from pydantic import Field

from modstack.artifacts import Artifact
from modstack.artifacts.messages import HumanMessage, MessageArtifact, SystemMessage
from modstack.typing import Schema

class LLMPrompt:
    messages: list[MessageArtifact]

    def __init__(
        self,
        prompt: Union[str, Artifact, list[MessageArtifact]],
        **kwargs
    ):
        if isinstance(prompt, str):
            self.messages = [HumanMessage(prompt, **kwargs)]
        elif isinstance(prompt, Artifact):
            self.messages = [HumanMessage(str(prompt), **kwargs)]
        else:
            self.messages = prompt

    @property
    def prompt(self) -> MessageArtifact:
        return self.messages[-1]

    @property
    def history(self) -> list[MessageArtifact]:
        return [
            message
            for message in self.messages[:-1]
            if not isinstance(message, SystemMessage)
        ]

    def __add__(self, other: 'LLMPrompt') -> 'LLMPrompt':
        self.messages += other.messages
        return self

class ZeroShotClassifierInput(Schema):
    artifact: Artifact
    labels: list[str] = Field(default_factory=list)

class PredictedLabel(NamedTuple):
    label: str
    score: float