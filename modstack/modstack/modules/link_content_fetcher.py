from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Callable

import requests
from tenacity import RetryCallState, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from modstack.commands import FetchFromLinks, command
from modstack.modules import Module
from modstack.typing import ByteStream
from modstack.version import __version__

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = f'modstack/LinkContentFetcher/{__version__}'
REQUEST_HEADERS = {
    'accept': '*/*',
    'User-Agent': DEFAULT_USER_AGENT,
    'Accept-Language': 'en-US,en;q=0.9,it;q=0.8,es;q=0.7',
    'referer': 'https://www.google.com/',
}

class LinkContentFetcher(Module):
    headers: dict[str, str]
    user_agents: list[str]
    max_workers: int | None
    retry_attempts: int
    wait_multiplier: int
    wait_min: int
    wait_max: int
    timeout: int
    raise_on_failure: bool

    def __init__(
        self,
        headers: dict[str, str] | None = None,
        user_agents: list[str] | None = None,
        max_workers: int | None = None,
        retry_attempts: int = 2,
        wait_multiplier: int = 1,
        wait_min: int = 2,
        wait_max: int = 10,
        timeout: int = 3,
        raise_on_failure: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.headers = headers or REQUEST_HEADERS
        self.user_agents = user_agents or [DEFAULT_USER_AGENT]
        self.max_workers = max_workers
        self.retry_attempts = retry_attempts
        self.wait_multiplier = wait_multiplier
        self.wait_min = wait_min
        self.timeout = timeout
        self.raise_on_failure = raise_on_failure
        self._current_user_agent_idx = 0
        self._response_handlers: dict[str | None, Callable[[requests.Response], ByteStream]] = {
            'text/html': _text_content_handler,
            'text/plain': _text_content_handler,
            'application/pdf': _binary_content_handler,
            'application/octet-stream': _binary_content_handler,
            None: _binary_content_handler
        }

        @retry(
            reraise=True,
            retry=retry_if_exception_type((requests.HTTPError, requests.RequestException)),
            stop=stop_after_attempt(self.retry_attempts),
            wait=wait_exponential(multiplier=self.wait_multiplier, min=self.wait_min, max=self.wait_max),
            after=self._switch_user_agent
        )
        def get_response(url: str) -> requests.Response:
            headers = self.headers.copy()
            headers['User-Agent'] = self.user_agents[self._current_user_agent_idx]
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response
        self._get_response = get_response

    @command(FetchFromLinks, name='fetch_from_links')
    def fetch(self, urls: list[str], **kwargs) -> list[ByteStream]:
        streams: list[ByteStream] = []

        if not urls:
            return streams

        if len(urls) == 1:
            streams.append(self._fetch(urls[0]))
        else:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                results = executor.map(self._fetch_with_exception_suppression, urls)
                for result in results:
                    if not result.is_empty():
                        streams.append(result)

        return streams

    def _fetch(self, url: str) -> ByteStream:
        content_type = 'text/html'
        stream = ByteStream(b'', content_type, metadata={})

        try:
            response = self._get_response(url)
            content_type = _get_content_type(response)
            stream = self._response_handlers[content_type](response)
            stream.metadata.update({'url': url, 'content_type': content_type})
        except Exception as e:
            if self.raise_on_failure:
                raise e
            logger.warning(f"Couldn't retrieve content from {url}. Error: {e}.")
        finally:
            self._current_user_agent_idx = 0

        return stream

    def _fetch_with_exception_suppression(self, url: str) -> ByteStream:
        if self.raise_on_failure:
            try:
                return self._fetch(url)
            except Exception as e:
                logger.warning(f'Error fetching url: {e}.')
                content_type = 'Unknown'
                return ByteStream(
                    b'',
                    content_type,
                    metadata={'url': url, 'content_type': content_type}
                )
        return self._fetch(url)

    def _switch_user_agent(self, retry_state: RetryCallState) -> None:
        self._current_user_agent_idx = (self._current_user_agent_idx + 1) % len(self.user_agents)
        logger.debug(f'Switched User Agent to {self.user_agents[self._current_user_agent_idx]}')

def _text_content_handler(response: requests.Response) -> ByteStream:
    return ByteStream.from_text(response.text, _get_content_type(response))

def _binary_content_handler(response: requests.Response) -> ByteStream:
    return ByteStream(response.content, _get_content_type(response))

def _get_content_type(response: requests.Response) -> str:
    return response.headers.get('Content-Type', '').split(';')[0]