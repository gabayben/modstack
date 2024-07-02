import json
from typing import Any, Iterator

import requests

from modstack.core import Modules
from modstack.artifacts.messages import AiMessageChunk, MessageChunk, MessageType
from modstack.ai import LLMPrompt

class OllamaLLM(Modules.Stream[LLMPrompt, MessageChunk]):
    def __init__(
        self,
        url: str = 'http://localhost:11434/api/generate',
        model: str = 'llama3',
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

    def _iter(
        self,
        prompt: LLMPrompt,
        role: MessageType = MessageType.HUMAN,
        images: list[str] | None = None,
        system_prompt: str | None = None,
        template: str | None = None,
        timeout: int | None = None,
        raw: bool | None = None,
        stream: bool | None = None,
        **kwargs
    ) -> Iterator[list[MessageChunk]]:
        generation_args = {**self.generation_args, **kwargs, 'stream': True}
        system_prompt = system_prompt or self.system_prompt
        template = template or self.template
        timeout = timeout or self.timeout
        raw = raw if raw is not None else self.raw

        payload = {
            'prompt': str(prompt.prompt),
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
            yield AiMessageChunk(
                chunk.get('response'),
                metadata={key: value for key, value in chunk.items() if key != 'response'}
            )