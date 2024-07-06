from abc import ABC, abstractmethod
from functools import partial
from typing import Optional, final

from modstack.ai import LLM
from modstack.artifacts import Artifact
from modstack.config import Settings
from modstack.core import SerializableModule
from modstack.query.synthesizers import SynthesizerInput
from modstack.typing import Effect, Effects

class _SummarySynthesizer(SerializableModule[SynthesizerInput, Artifact], ABC):
    @final
    def forward(self, data: SynthesizerInput, **kwargs) -> Effect[Artifact]:
        return Effects.From(
            invoke=partial(self._invoke, data, **kwargs),
            ainvoke=partial(self._ainvoke, data, **kwargs)
        )

    @abstractmethod
    def _invoke(self, data: SynthesizerInput, **kwargs) -> Artifact:
        pass

    @abstractmethod
    async def _ainvoke(self, data: SynthesizerInput, **kwargs) -> Artifact:
        pass

class LLMSummarySynthesizer(_SummarySynthesizer):
    llm: LLM

    def __init__(self, llm: Optional[LLM] = None, **kwargs):
        llm = llm or Settings.llm
        super().__init__(llm=llm, **kwargs)

    def _invoke(self, data: SynthesizerInput, **kwargs) -> Artifact:
        pass

    async def _ainvoke(self, data: SynthesizerInput, **kwargs) -> Artifact:
        pass