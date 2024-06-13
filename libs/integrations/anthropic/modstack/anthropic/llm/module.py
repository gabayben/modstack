from typing import Any, Iterable, Iterator, Mapping

from anthropic import Anthropic, NOT_GIVEN
from anthropic.types import ContentBlockDeltaEvent, MessageDeltaEvent, MessageStartEvent

from modstack.auth import Secret
from modstack.modules import Modules

from modstack.artifacts.messages import ChatMessage, ChatMessageChunk, ChatRole
from modstack.modules.ai import LLMRequest

class AnthropicLLM(Modules.Stream[LLMRequest, list[ChatMessageChunk]]):
    def __init__(
        self,
        token: Secret = Secret.from_env_var('ANTHROPIC_API_KEY'),
        base_url: str | None = None,
        default_query: Mapping[str, object] | None = None,
        default_headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
        model: str = 'claude-3-sonnet-20240229',
        generation_args: dict[str, Any] | None = None,
        max_tokens: int = 512,
        system_prompt: str | None = None,
        top_k: int | None = None,
        top_p: float | None = None,
        temperature: float | None = None,
        stop_sequences: list[str] | None = None
    ):
        self.client = Anthropic(
            api_key=token.resolve_value(),
            base_url=base_url,
            default_query=default_query,
            default_headers=default_headers,
            timeout=timeout or NOT_GIVEN
        )
        self.model = model
        self.generation_args = generation_args or {}
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.top_k = top_k
        self.top_p = top_p
        self.temperature = temperature
        self.stop_sequences = stop_sequences

    def _iter(
        self,
        data: LLMRequest,
        role: ChatRole = ChatRole.USER,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        top_k: int | None = None,
        top_p: float | None = None,
        temperature: float | None = None,
        stop_sequences: list[str] | None = None,
        **kwargs
    ) -> Iterator[list[ChatMessageChunk]]:
        generation_args = {**self.generation_args, **kwargs}
        generation_args.update({'stream': True})
        max_tokens = max_tokens or self.max_tokens
        system_prompt = system_prompt or self.system_prompt
        top_k = top_k or self.top_k
        top_p = top_p or self.top_p
        temperature = temperature or self.temperature
        stop_sequences = stop_sequences or self.stop_sequences

        history = data.history or []
        history.append(ChatMessageChunk(data.prompt, role))
        formatted_messages = _convert_to_anthropic_format(history)

        response = self.client.messages.create(
            max_tokens=max_tokens,
            messages=formatted_messages,
            model=self.model,
            system=system_prompt,
            top_k=top_k,
            top_p=top_p,
            temperature=temperature,
            stop_sequences=stop_sequences,
            stream=True,
            **generation_args
        )

        completions: list[ChatMessageChunk] = []
        message_start: MessageStartEvent | None = None
        delta: MessageDeltaEvent | None = None
        for stream_event in response:
            if isinstance(stream_event, MessageStartEvent):
                message_start = stream_event
            if isinstance(stream_event, MessageDeltaEvent):
                delta = stream_event
            if isinstance(stream_event, ContentBlockDeltaEvent):
                chunk = ChatMessageChunk(stream_event.delta.text or '', ChatRole.ASSISTANT)
                chunk.metadata.update({
                    'model': self.model,
                    'index': stream_event.index,
                    'finish_reason': delta.delta.stop_reason if delta else 'end_turn',
                    'usage': dict(message_start.message.usage, **dict(delta.usage)) if message_start and delta else {}
                })
                yield [chunk]

def _convert_to_anthropic_format(messages: Iterable[ChatMessage]) -> list[dict[str, Any]]:
    formatted_messages: list[dict[str, Any]] = []
    for message in messages:
        message_dict = dict(message)
        formatted_messages.append(
            {k: v for k, v in message_dict.items() if k in ['content', 'role'] and v}
        )
    return formatted_messages