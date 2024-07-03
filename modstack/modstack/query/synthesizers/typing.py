from modstack.artifacts import Artifact
from modstack.core import Module
from modstack.typing import Schema

class Synthesis(Schema):
    query: Artifact
    chunks: list[Artifact]

    def __init__(
        self,
        query: Artifact,
        chunks: list[Artifact],
        **kwargs
    ):
        super().__init__(query=query, chunks=chunks, **kwargs)

Synthesizer = Module[Synthesis, Artifact]