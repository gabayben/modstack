from typing import Any, Iterable, Mapping

from anthropic import Anthropic, NOT_GIVEN, Stream
from anthropic.types import ContentBlockDeltaEvent, Message, MessageDeltaEvent, MessageStartEvent, TextBlock

from modstack.auth import Secret

from modstack.modules import Modules
from modstack.typing import ChatMessage, ChatRole, StreamingCallback, StreamingChunk
from modstack_anthropic.llm import AnthropicLLMRequest

class AnthropicLLM(Modules.Sync[AnthropicLLMRequest, Iterable[ChatMessage]]):
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

    def _invoke(self, data: AnthropicLLMRequest, **kwargs) -> Iterable[ChatMessage]:
        generation_args = {**self.generation_args, **(data.model_extra or {})}
        max_tokens = data.max_tokens or self.max_tokens
        system_prompt = data.system_prompt or self.system_prompt
        top_k = data.top_k or self.top_k
        top_p = data.top_p or self.top_p
        temperature = data.temperature or self.temperature
        stop_sequences = data.stop_sequences or self.stop_sequences
        stream = data.stream if data.stream is not None else self.stream

        history = data.history or []
        history.append(ChatMessage(data.prompt, data.role or ChatRole.USER))
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
            stream=stream,
            **generation_args
        )

        completions: list[ChatMessage] = []
        if isinstance(response, Stream):
            chunks: list[StreamingChunk] = []
            stream_event, delta, message_start = None, None, None
            for stream_event in response:
                if isinstance(stream_event, MessageStartEvent):
                    message_start = stream_event
                if isinstance(stream_event, ContentBlockDeltaEvent):
                    chunk = (stream_event.delta.text, {})
                    chunks.append(chunk)
                    if self.streaming_callback:
                        self.streaming_callback(chunk[0], chunk[1])
                if isinstance(stream_event, MessageDeltaEvent):
                    delta = stream_event
            completions = [self._connect_chunks(chunks, message_start, delta)]
        elif isinstance(response, Message):
            completions = [self._build_message(response, block) for block in response.content]

        return completions

    def _connect_chunks(
        self,
        chunks: list[StreamingChunk],
        message_start: MessageStartEvent,
        delta: MessageDeltaEvent
    ) -> ChatMessage:
        complete_response = ChatMessage.from_assistant(''.join(chunk[0] for chunk in chunks))
        complete_response.metadata.update({
            'model': self.model,
            'index': 0,
            'finish_reason': delta.delta.stop_reason if delta else 'end_turn',
            'usage': dict(message_start.message.usage, **dict(delta.usage)) if message_start and delta else {}
        })
        return complete_response

    def _build_message(self, message: Message, block: TextBlock) -> ChatMessage:
        result = ChatMessage.from_assistant(block.text)
        result.metadata.update({
            'model': self.model,
            'index': 0,
            'finish_reason': message.stop_reason,
            'usage': dict(message.usage or {})
        })
        return result

def _convert_to_anthropic_format(messages: Iterable[ChatMessage]) -> list[dict[str, Any]]:
    formatted_messages: list[dict[str, Any]] = []
    for message in messages:
        message_dict = dict(message)
        formatted_messages.append(
            {k: v for k, v in message_dict.items() if k in ['content', 'role'] and v}
        )
    return formatted_messages