from typing import Union

from modstack.artifacts import Utf8Artifact
from modstack.artifacts.messages import HumanMessage, MessageArtifact

class LLMPrompt:
    messages: list[MessageArtifact]

    def __init__(
        self,
        prompt: Union[str, Utf8Artifact, list[MessageArtifact]],
        **kwargs
    ):
        if isinstance(prompt, str):
            self.messages = [HumanMessage(prompt, **kwargs)]
        elif isinstance(prompt, Utf8Artifact):
            self.messages = [HumanMessage(str(prompt), **kwargs)]
        else:
            self.messages = prompt

    @property
    def prompt(self) -> MessageArtifact:
        return self.messages[-1]

    @property
    def history(self) -> list[MessageArtifact]:
        return self.messages[1:] if len(self.messages) > 1 else []

    def __add__(self, other: 'LLMPrompt') -> 'LLMPrompt':
        self.messages += other.messages
        return self