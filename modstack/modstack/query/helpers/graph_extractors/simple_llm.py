from functools import partial

from modstack.ai import LLM
from modstack.artifacts import Artifact
from modstack.config import Settings
from modstack.core import SerializableModule
from modstack.typing import Effect, Effects

class SimpleLLMGraphExtractor(SerializableModule[list[Artifact], list[Artifact]]):
    llm: LLM

    def __init__(self, llm: LLM = Settings.llm, **kwargs):
        super().__init__(llm=llm, **kwargs)

    def forward(self, artifacts: list[Artifact], **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(self._invoke, artifacts, **kwargs),
            ainvoke=partial(self._ainvoke, artifacts, **kwargs)
        )

    def _invoke(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        pass

    async def _ainvoke(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        pass