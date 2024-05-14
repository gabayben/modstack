from typing import Any, Iterator, Mapping

from anthropic import Anthropic, NOT_GIVEN

from modstack.auth import Secret
from modstack.commands import LLMCommand, command
from modstack.modules import Module
from modstack.typing import ChatMessage, StreamingCallback
from modstack_anthropic.llm import AnthropicLLMCommand

class AnthropicLLM(Module):
    def __init__(
        self,
        token: Secret = Secret.from_env_var('ANTHROPIC_API_KEY'),
        base_url: str | None = None,
        default_query: Mapping[str, object] | None = None,
        default_headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
        model: str = 'claude-3-sonnet-20240229',
        streaming_callback: StreamingCallback | None = None,
        generation_args: dict[str, Any] | None = None,
        max_tokens: int = 512,
        system_prompt: str | None = None,
        top_k: int | None = None,
        top_p: float | None = None,
        temperature: float | None = None,
        stop_sequences: list[str] | None = None,
        stream: bool = False
    ):
        super().__init__()
        self.client = Anthropic(
            api_key=token.resolve_value(),
            base_url=base_url,
            default_query=default_query,
            default_headers=default_headers,
            timeout=timeout or NOT_GIVEN
        )
        self.model = model
        self.streaming_callback = streaming_callback
        self.generation_args = generation_args or {}
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.top_k = top_k
        self.top_p = top_p
        self.temperature = temperature
        self.stop_sequences = stop_sequences
        self.stream = stream

    @command(LLMCommand)
    def call(
        self,
        messages: list[ChatMessage],
        generation_args: dict[str, Any] | None = None,
        **kwargs
    ) -> Iterator[ChatMessage]:
        yield from self.anthropic_call(messages, generation_args, **kwargs)

    @command(AnthropicLLMCommand)
    def anthropic_call(
        self,
        messages: list[ChatMessage],
        generation_args: dict[str, Any] | None = None,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        top_k: int | None = None,
        top_p: float | None = None,
        temperature: float | None = None,
        stop_sequences: list[str] | None = None,
        stream: bool = False,
        **kwargs
    ) -> Iterator[ChatMessage]:
        if not messages:
            yield from []

        generation_args = {**self.generation_args, **(generation_args or {})}
        max_tokens = max_tokens or self.max_tokens
        system_prompt = system_prompt or self.system_prompt
        top_k = top_k or self.top_k
        top_p = top_p or self.top_p
        temperature = temperature or self.temperature
        stop_sequences = stop_sequences or self.stop_sequences
        stream = stream if stream is not None else self.stream