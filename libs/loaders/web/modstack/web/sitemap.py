from modstack.artifacts import Utf8Artifact
from modstack.modules import Modules

class SitemapFetcher(Modules.Sync[str, list[Utf8Artifact]]):
    def _invoke(self, url: str, **kwargs) -> list[Utf8Artifact]:
        pass