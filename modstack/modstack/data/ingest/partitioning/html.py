from modstack.artifacts import Artifact
from modstack.artifacts.layout import Element
from modstack.modules import module

@module
def html_partitioner(html: Artifact, **kwargs) -> list[Element]:
    pass