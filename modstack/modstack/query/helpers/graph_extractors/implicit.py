from modstack.artifacts import Artifact
from modstack.core import Modules

class ImplicitGraphExtractor(Modules.Sync[list[Artifact], list[Artifact]]):
    def _invoke(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        pass