import json
from typing import Any, ClassVar

import requests

from modstack.auth import Secret
from modstack.contracts.websearch import SearchEngineResponse
from modstack.modules import Modules
from modstack.typing import LinkArtifact, TextArtifact
from modstack.utils.display import mapping_to_str
from modstack_serper.search import SerperError, SerperSearchQuery, SerperSearchResponse
from modstack_serper.search.builders import build_search_response

class _SerperSearch:
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

class SerperSearch:
    class Search(Modules.Sync[SerperSearchQuery, SearchEngineResponse], _SerperSearch):
        def _invoke(self, data: SerperSearchQuery) -> SearchEngineResponse:
            search = SerperSearch.NativeSearch(
                api_key=self.api_key,
                allowed_domains=self.allowed_domains,
                search_params=self.search_params,
                country=self.country,
                language=self.language,
                autocomplete=self.autocomplete,
                timeout=self.timeout
            )
            return SerperSearch.Map().forward(
                search.forward(data).invoke()
            ).invoke()

    class NativeSearch(Modules.Sync[SerperSearchQuery, SerperSearchResponse], _SerperSearch):
        SERPER_BASE_URL: ClassVar[str] = 'https://google.serper.dev/search'

        def _invoke(self, data: SerperSearchQuery) -> SerperSearchResponse:
            allowed_domains = data.allowed_domains
            search_params = data.search_params
            query = data.query
            country = data.country
            language = data.language
            autocomplete = data.autocomplete

            if allowed_domains:
                allowed_domains = self.allowed_domains + allowed_domains if self.allowed_domains else allowed_domains
            else:
                allowed_domains = self.allowed_domains
            search_params = {**self.search_params, **{search_params or {}}}
            query_prepend = 'OR '.join(
                f'site:{domain}' for domain in self.allowed_domains) if self.allowed_domains else ''

            payload = json.dumps({
                'q': query_prepend + query,
                'gl': country or self.country,
                'hl': language or self.language,
                'autocorrect': autocomplete if autocomplete is not None else self.autocomplete,
                **search_params
            })
            headers = {'X-API-KEY': self.api_key.resolve_value(), 'Content-Type': 'application/json'}

            try:
                response = requests.post(self.SERPER_BASE_URL, data=payload, headers=headers, timeout=self.timeout)
                response.raise_for_status()
            except requests.Timeout as e:
                raise TimeoutError(f'Request to {self.SERPER_BASE_URL} with payload {payload} timed out.') from e
            except requests.RequestException as e:
                raise SerperError(f'An error occurred while querying. Payload {payload}, Error: {e}.') from e

            return build_search_response(response.json())

    class Map(Modules.Sync[SerperSearchResponse, SearchEngineResponse]):
        def _invoke(self, data: SerperSearchResponse) -> SearchEngineResponse:
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
                for result in data.response.organic
            ]

            content: list[TextArtifact] = []

            if data.response.knowledge_graph:
                content.append(
                    TextArtifact(
                        'Google Search Knowledge Graph:\n'
                        + mapping_to_str(dict(data.response.knowledge_graph))
                    )
                )

            if data.response.people_also_ask:
                entries_str = ''
                for entry in data.response.people_also_ask:
                    entries_str += f'{entry.get('question')}\n'
                    entries_str += mapping_to_str(dict(entry), exclude=['question']) + '\n'
                content.append(
                    TextArtifact('People Also Ask:\n' + entries_str.strip('\n'))
                )

            if data.response.related_searches:
                content.append(
                    TextArtifact(f"Related Searches: {', '.join(data.response.related_searches)}")
                )

            return SearchEngineResponse(links=links, content=content)