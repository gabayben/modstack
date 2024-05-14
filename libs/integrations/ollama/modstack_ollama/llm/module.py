import json
from typing import Any

import requests

from modstack.commands import LLMCommand, command
from modstack.modules import Module
from modstack.typing import ChatMessage, StreamingCallback, StreamingChunk
from modstack_ollama.llm import OllamaLLMCommand

class OllamaLLM(Module):
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

    @command(LLMCommand)
    def generate(
        self,
        messages: list[ChatMessage],
        generation_args: dict[str, Any] | None = None,
        **kwargs
    ) -> list[ChatMessage]:
        return self.ollama_generate(messages, generation_args=generation_args, **kwargs)

    @command(OllamaLLMCommand)
    def ollama_generate(
        self,
        messages: list[ChatMessage],
        generation_args: dict[str, Any] | None = None,
        images: list[str] | None = None,
        system_prompt: str | None = None,
        template: str | None = None,
        timeout: int | None = None,
        raw: bool | None = None,
        **kwargs
    ) -> list[ChatMessage]:
        generation_args = {**(generation_args or {})}
        system_prompt = system_prompt or self.system_prompt
        template = template or self.template
        timeout = timeout or self.timeout
        raw = raw if raw is not None else self.raw
        stream = self.streaming_callback is not None

        for message in messages:
            payload = {
                'prompt': message.content,
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