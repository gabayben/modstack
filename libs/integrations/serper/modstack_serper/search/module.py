import logging
from typing import Any

from modstack.auth import Secret
from modstack.commands import command
from modstack.commands.websearch import SearchEngineQuery, SearchEngineResponse
from modstack.modules import Module
from modstack_serper.search import SerperSearchQuery, SerperSearchResponse

SERPER_BASE_URL = 'https://google.serper.dev/search'
logger = logging.getLogger(__name__)

class SerperSearch(Module):
    def __init__(
        self,
        api_key: Secret = Secret.from_env_var('SERPERDEV_API_KEY'),
        allowed_domains: list[str] | None = None,
        search_params: dict[str, Any] | None = None
    ):
        self.api_key = api_key
        self.allowed_domains = allowed_domains
        self.search_params = search_params or {}
        _ = self.api_key.resolve_value()

    @command(SearchEngineQuery, name='serper_search')
    def search(
        self,
        query: str,
        allowed_domains: list[str] | None = None,
        search_params: dict[str, Any] | None = None,
        **kwargs
    ) -> SearchEngineResponse:
        pass

    @command(SerperSearchQuery)
    def serper_search(
        self,
        query: str,
        allowed_domains: list[str] | None = None,
        search_params: dict[str, Any] | None = None,
        **kwargs
    ) -> SerperSearchResponse:
        query_prepend = 'OR '.join(f'site:{domain}' for domain in self.allowed_domains) if self.allowed_domains else ''