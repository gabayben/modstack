from modstack.modules import Modules
from modstack.reddit import RedditDocument, RedditQuery

class RedditConnector(Modules.Sync[RedditQuery, list[RedditDocument]]):
    def _invoke(self, query: RedditQuery, **kwargs) -> list[RedditDocument]:
        pass