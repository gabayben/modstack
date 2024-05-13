import json
from typing import Any, Callable

import requests

from modstack.containers import feature
from modstack.contracts import GenerateText, TextGeneration
from modstack.modules import Module
from modstack_ollama.text import OllamaGenerateText

StreamingChunk = tuple[str, dict[str, Any]]
StreamingCallback = Callable[[str, dict[str, Any]], None]

class OllamaTextGenerator(Module):
    def __init__(
        self,
        url: str = 'http://localhost:11434/api/generate',
        model: str = 'orca-mini',
        system_prompt: str | None = None,
        template: str | None = None,
        timeout: int = 120,
        raw: bool = False,
        streaming_callback: StreamingCallback | None = None
    ):
        super().__init__()
        self.url = url
        self.model = model
        self.system_prompt = system_prompt
        self.template = template
        self.timeout = timeout
        self.raw = raw
        self.streaming_callback = streaming_callback

    @feature(name=GenerateText.name())
    def generate(
        self,
        prompt: str,
        generation_args: dict[str, Any] | None = None,
        **kwargs
    ) -> TextGeneration:
        return self.ollama_generate(prompt, generation_args=generation_args, **kwargs)

    @feature(name=OllamaGenerateText.name())
    def ollama_generate(
        self,
        prompt: str,
        generation_args: dict[str, Any] | None = None,
        images: list[str] | None = None,
        system_prompt: str | None = None,
        template: str | None = None,
        timeout: int | None = None,
        raw: bool | None = None,
        **kwargs
    ) -> TextGeneration:
        generation_args = {**(generation_args or {})}
        system_prompt = system_prompt or self.system_prompt
        template = template or self.template
        timeout = timeout or self.timeout
        raw = raw if raw is not None else self.raw
        stream = self.streaming_callback is not None

        payload = {
            'prompt': prompt,
            'model': self.model,
            'system': system_prompt,
            'template': template,
            'raw': raw,
            'stream': stream,
            'options': generation_args
        }

        response = requests.post(self.url, json=payload, timeout=self.timeout, stream=stream)
        response.raise_for_status()

        if stream:
            chunks: list[StreamingChunk] = []
            for line in response.iter_lines():
                chunk = _build_chunk(line)
                chunks.append(chunk)
                if self.streaming_callback:
                    self.streaming_callback(chunk[0], chunk[1])
            return TextGeneration(
                results=[''.join(content for content, _ in chunks)],
                metadata=[{key: value for key, value in chunks[0][1].items() if key != 'response'}]
            )

        data = response.json()
        return TextGeneration(
            results=[data['response']],
            metadata=[{key: value for key, value in data if key != 'response'}]
        )

def _build_chunk(data: bytes | bytearray) -> StreamingChunk:
    chunk = json.loads(data.decode(encoding='utf-8'))
    return (
        chunk['response'],
        {key: value for key, value in chunk.items() if key != 'response'}
    )