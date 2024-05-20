import json
from typing import Any, Iterable

import requests

from modstack.modules import Modules
from modstack.typing import ChatMessage, StreamingCallback, StreamingChunk
from modstack_ollama.llm import CallOllamaLLM

class OllamaLLM(Modules.Sync[CallOllamaLLM, Iterable[ChatMessage]]):
    def __init__(
        self,
        url: str = 'http://localhost:11434/api/generate',
        model: str = 'orca-mini',
        system_prompt: str | None = None,
        template: str | None = None,
        timeout: int = 120,
        raw: bool = False,
        streaming_callback: StreamingCallback | None = None,
        stream: bool = False,
        generation_args: dict[str, Any] = {}
    ):
        super().__init__()
        self.url = url
        self.model = model
        self.system_prompt = system_prompt
        self.template = template
        self.timeout = timeout
        self.raw = raw
        self.streaming_callback = streaming_callback
        self.stream = stream
        self.generation_args = generation_args

    def _invoke(self, data: CallOllamaLLM) -> Iterable[ChatMessage]:
        generation_args = {**self.generation_args, **(data.generation_args or {})}
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

        if stream:
            chunks: list[StreamingChunk] = []
            for line in response.iter_lines():
                chunk = _build_chunk(line)
                chunks.append(chunk)
                if self.streaming_callback:
                    self.streaming_callback(chunk[0], chunk[1])
            return [ChatMessage.from_assistant(
                ''.join(content for content, _ in chunks),
                metadata={key: value for key, value in chunks[0][1].items() if key != 'response'}
            )]

        data = response.json()
        return [ChatMessage.from_assistant(
            data['response'],
            metadata={key: value for key, value in data if key != 'response'}
        )]

def _build_chunk(data: bytes | bytearray) -> StreamingChunk:
    chunk = json.loads(data.decode(encoding='utf-8'))
    return (
        chunk['response'],
        {key: value for key, value in chunk.items() if key != 'response'}
    )