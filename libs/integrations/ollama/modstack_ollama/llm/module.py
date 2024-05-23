import json
from typing import Any, Iterator

import requests

from modstack.modules import Modules
from modstack.typing.messages import ChatMessageChunk, ChatRole
from modstack_ollama.llm import OllamaLLMRequest

class OllamaLLM(Modules.Stream[OllamaLLMRequest, ChatMessageChunk]):
    def __init__(
        self,
        url: str = 'http://localhost:11434/api/generate',
        model: str = 'orca-mini',
        system_prompt: str | None = None,
        template: str | None = None,
        timeout: int = 120,
        raw: bool = False,
        generation_args: dict[str, Any] = {}
    ):
        super().__init__()
        self.url = url
        self.model = model
        self.system_prompt = system_prompt
        self.template = template
        self.timeout = timeout
        self.raw = raw
        self.generation_args = generation_args

    def _iter(self, data: OllamaLLMRequest, **kwargs) -> Iterator[ChatMessageChunk]:
        generation_args = {**self.generation_args, **(data.model_extra or {}), 'stream': True}
        system_prompt = data.system_prompt or self.system_prompt
        template = data.template or self.template
        timeout = data.timeout or self.timeout
        raw = data.raw if data.raw is not None else self.raw

        payload = {
            'prompt': data.prompt,
            'model': self.model,
            'system': system_prompt,
            'template': template,
            'raw': raw,
            'stream': True,
            'options': generation_args
        }

        response = requests.post(self.url, json=payload, timeout=self.timeout, stream=True)
        response.raise_for_status()

        for line in response.iter_lines():
            chunk = json.load(line.decode('utf-8'))
            yield ChatMessageChunk(
                chunk['response'],
                ChatRole.ASSISTANT,
                metadata={key: value for key, value in chunk.items() if key != 'response'}
            )