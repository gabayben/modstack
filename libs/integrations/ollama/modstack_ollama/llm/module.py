from typing import Any

import requests

from modstack.modules import Modules
from modstack.typing.messages import ChatMessageChunk, ChatRole
from modstack_ollama.llm import OllamaLLMRequest

class OllamaLLM(Modules.Sync[OllamaLLMRequest, ChatMessageChunk]):
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

    def _invoke(self, data: OllamaLLMRequest, **kwargs) -> ChatMessageChunk:
        generation_args = {**self.generation_args, **(data.model_extra or {})}
        system_prompt = data.system_prompt or self.system_prompt
        template = data.template or self.template
        timeout = data.timeout or self.timeout
        raw = data.raw if data.raw is not None else self.raw
        stream = data.stream if data.stream is not None else self.stream

        payload = {
            'prompt': data.prompt,
            'model': self.model,
            'system': system_prompt,
            'template': template,
            'raw': raw,
            'stream': stream,
            'options': generation_args
        }

        response = requests.post(self.url, json=payload, timeout=self.timeout, stream=stream)
        response.raise_for_status()

        data = response.json()
        return ChatMessageChunk(
            data['response'],
            ChatRole.ASSISTANT,
            metadata={key: value for key, value in data if key != 'response'}
        )