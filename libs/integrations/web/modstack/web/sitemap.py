from modstack.core.artifacts import Utf8Artifact
from modstack.core.modules import Modules

class SitemapFetcher(Modules.Sync[str, list[Utf8Artifact]]):
    def _invoke(self, url: str, **kwargs) -> list[Utf8Artifact]:
        pass