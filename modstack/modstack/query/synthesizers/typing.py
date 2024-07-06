from modstack.artifacts import Artifact
from modstack.core import Module, ModuleLike
from modstack.typing import Schema

class SynthesizerInput(Schema):
    query: Artifact
    chunks: list[Artifact]

    def __init__(
        self,
        query: Artifact,
        chunks: list[Artifact],
        **kwargs
    ):
        super().__init__(query=query, chunks=chunks, **kwargs)

SynthesizerLike = ModuleLike[SynthesizerInput, Artifact]
Synthesizer = Module[SynthesizerInput, Artifact]