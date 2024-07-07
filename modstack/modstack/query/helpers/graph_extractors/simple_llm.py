from functools import partial

from modstack.ai import LLM
from modstack.ai.prompts import EXTRACT_TRIPLETS_PROMPT
from modstack.artifacts import Artifact
from modstack.config import Settings
from modstack.core import Module, ModuleLike, SerializableModule, coerce_to_module
from modstack.query.helpers import default_triplet_parser
from modstack.typing import Effect, Effects

class SimpleLLMGraphExtractor(SerializableModule[list[Artifact], list[Artifact]]):
    llm: LLM
    prompt_template: str
    triplet_parser: Module[str, tuple[str, str, str]]
    max_paths_per_chunk: int
    num_workers: int

    def __init__(
        self,
        llm: LLM = Settings.llm,
        prompt_template: str = EXTRACT_TRIPLETS_PROMPT,
        triplet_parser: ModuleLike[str, tuple[str, str, str]] = default_triplet_parser,
        max_paths_per_chunk: int = 10,
        num_workers: int = 4,
        **kwargs
    ):
        super().__init__(
            llm=llm,
            prompt_template=prompt_template,
            triplet_parser=coerce_to_module(triplet_parser),
            max_paths_per_chunk=max_paths_per_chunk,
            num_workers=num_workers,
            **kwargs
        )

    def forward(self, artifacts: list[Artifact], **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(self._invoke, artifacts, **kwargs),
            ainvoke=partial(self._ainvoke, artifacts, **kwargs)
        )

    def _invoke(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        pass

    async def _ainvoke(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        pass