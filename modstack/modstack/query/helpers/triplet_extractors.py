from functools import partial
from typing import Optional, final

from modstack.ai import LLM
from modstack.ai.prompts import EXTRACT_TRIPLETS_PROMPT
from modstack.artifacts import Artifact
from modstack.core import SerializableModule
from modstack.stores import GraphTriplet
from modstack.config import Settings
from modstack.typing import Effect, Effects

class LLMTripletExtractor(SerializableModule[Artifact, list[GraphTriplet]]):
    llm: LLM
    prompt_template: str
    max_object_length: int

    def __init__(
        self,
        llm: Optional[LLM] = None,
        prompt_template: Optional[str] = None,
        max_object_length: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            llm=llm or Settings.llm,
            prompt_template=prompt_template or EXTRACT_TRIPLETS_PROMPT,
            max_object_length=max_object_length or 128,
            **kwargs
        )

    @final
    def forward(self, artifact: Artifact, **kwargs) -> Effect[list[GraphTriplet]]:
        return Effects.From(
            invoke=partial(self._invoke, artifact, **kwargs),
            ainvoke=partial(self._ainvoke, artifact, **kwargs)
        )

    def _invoke(self, artifact: Artifact, **kwargs) -> list[GraphTriplet]:
        pass

    async def _ainvoke(self, artifact: Artifact, **kwargs) -> list[GraphTriplet]:
        pass

    @staticmethod
    def _parse_triplet_response(response: str, max_length: int = 128) -> list[GraphTriplet]:
        pass