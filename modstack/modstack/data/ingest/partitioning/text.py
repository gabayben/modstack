from modstack.artifacts import Artifact
from modstack.artifacts.layout import Element
from modstack.modules import module

@module
def text_partitioner(text: Artifact, **kwargs) -> list[Element]:
    pass