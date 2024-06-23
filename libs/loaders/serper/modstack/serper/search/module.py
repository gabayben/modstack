import json
from typing import Any

import requests

from modstack.artifacts import LinkArtifact, TextArtifact
from modstack.auth import Secret
from modstack.modules import Modules, SerializableModule
from modstack.typing.modules import SearchEngineResponse
from modstack.typing import Effect
from modstack.utils.string import mapping_to_str
from modstack.serper.constants import SERPER_SEARCH_URL
from modstack.serper.search import SerperError, SerperSearchResponse
from modstack.serper.search.builders import build_search_response

class _SerperSearch:
    api_key: Secret = Secret.from_env_var('SERPERDEV_API_KEY')
    allowed_domains: list[str] | None = None
    search_params: dict[str, Any] | None = None
    country: str = 'us'
    language: str = 'en'
    autocomplete: bool = True
    timeout: int = 30

class SerperSearch:
    class Search(SerializableModule[str, SearchEngineResponse], _SerperSearch):
        def forward(self, query: str, **kwargs) -> Effect[SearchEngineResponse]:
            return (
                SerperSearch.NativeSearch(
                    api_key=self.api_key,
                    allowed_domains=self.allowed_domains,
                    search_params=self.search_params,
                    country=self.country,
                    language=self.language,
                    autocomplete=self.autocomplete,
                    timeout=self.timeout
                )
                .map(SerperSearch.Map())
                .forward(query, **kwargs)
            )

    class NativeSearch(Modules.Sync[str, SerperSearchResponse], _SerperSearch):
        def _invoke(
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
                response = requests.post(SERPER_SEARCH_URL, data=payload, headers=headers, timeout=self.timeout)
                response.raise_for_status()
            except requests.Timeout as e:
                raise TimeoutError(f'Request to {SERPER_SEARCH_URL} with payload {payload} timed out.') from e
            except requests.RequestException as e:
                raise SerperError(f'An error occurred while querying. Payload {payload}, Error: {e}.') from e

            return build_search_response(response.json())

    class Map(Modules.Sync[SerperSearchResponse, SearchEngineResponse]):
        def _invoke(self, data: SerperSearchResponse, **kwargs) -> SearchEngineResponse:
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