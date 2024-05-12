import json
import logging
from typing import Any

import requests

from modstack.auth import Secret
from modstack.commands import command
from modstack.commands.websearch import SearchEngineQuery, SearchEngineResponse
from modstack.modules import Module
from modstack.typing import LinkArtifact, TextArtifact
from modstack.utils.display import mapping_to_str
from modstack_serper.search import SerperError, SerperSearchQuery, SerperSearchResponse
from modstack_serper.search.builders import build_search_response

SERPER_BASE_URL = 'https://google.serper.dev/search'
logger = logging.getLogger(__name__)

class SerperSearch(Module):
    def __init__(
        self,
        api_key: Secret = Secret.from_env_var('SERPERDEV_API_KEY'),
        allowed_domains: list[str] | None = None,
        search_params: dict[str, Any] | None = None,
        country: str = 'us',
        language: str = 'en',
        autocomplete: bool = True,
        timeout: int = 30
    ):
        self.api_key = api_key
        self.allowed_domains = allowed_domains
        self.search_params = search_params or {}
        self.country = country
        self.language = language
        self.autocomplete = autocomplete
        self.timeout = timeout
        _ = self.api_key.resolve_value()

    @command(SearchEngineQuery, name='serper_search')
    def search(self, query: str, **kwargs) -> SearchEngineResponse:
        serper_response = self.serper_search(query, **kwargs)

        links: list[LinkArtifact] = [
            LinkArtifact(
                link=result.get('link'),
                title=result.get('title'),
                position=result.get('position', None),
                description=result.get('snippet', None),
                metadata={
                    'date': result.get('date', None),
                    'image_url': result.get('image_url', None),
                    'site_links': result.get('site_links', None),
                    **result.get('attributes', {})
                }
            )
            for result in serper_response.organic
        ]
        content: list[TextArtifact] = []

        if serper_response.knowledge_graph:
            content.append(
                TextArtifact(mapping_to_str(dict(serper_response.knowledge_graph)))
            )
        if serper_response.people_also_ask:
            content.append(
                TextArtifact(mapping_to_str(dict(serper_response.people_also_ask))) #type: ignore[call-args]
            )
        if serper_response.related_searches:
            content.append(
                TextArtifact(f"Related Searches: {', '.join(serper_response.related_searches)}")
            )

        return SearchEngineResponse(links=links, content=content)

    @command(SerperSearchQuery)
    def serper_search(
        self,
        query: str,
        allowed_domains: list[str] | None = None,
        search_params: dict[str, Any] | None = None,
        country: str | None = None,
        language: str | None = None,
        autocomplete: bool | None = None,
        **kwargs
    ) -> SerperSearchResponse:
        if allowed_domains:
            allowed_domains = self.allowed_domains + allowed_domains if self.allowed_domains else allowed_domains
        else:
            allowed_domains = self.allowed_domains
        search_params = {**self.search_params, **{search_params or {}}}
        query_prepend = 'OR '.join(f'site:{domain}' for domain in self.allowed_domains) if self.allowed_domains else ''

        payload = json.dumps({
            'q': query_prepend + query,
            'gl': country or self.country,
            'hl': language or self.language,
            'autocorrect': autocomplete if autocomplete is not None else self.autocomplete,
            **search_params
        })
        headers = {'X-API-KEY': self.api_key.resolve_value(), 'Content-Type': 'application/json'}

        try:
            response = requests.post(SERPER_BASE_URL, data=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.Timeout as e:
            raise TimeoutError(f'Request to {SERPER_BASE_URL} with payload {payload} timed out.') from e
        except requests.RequestException as e:
            raise SerperError(f'An error occurred while querying. Payload {payload}, Error: {e}.') from e

        return build_search_response(response.json())