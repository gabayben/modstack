from typing import Any, ClassVar, Iterator

import cohere

from modstack.auth import Secret
from modstack.commands import LLMCommand, command
from modstack.modules import Module
from modstack.typing import ChatMessage, ChatRole, StreamingCallback
from modstack_cohere.utils import build_cohore_metadata

class CohereLLM(Module):
    ROLES_MAP: ClassVar[dict[ChatRole, cohere.ChatMessageRole]] = {
        ChatRole.USER: 'USER',
        ChatRole.FUNCTION: 'USER',
        ChatRole.ASSISTANT: 'CHAT',
        ChatRole.SYSTEM: 'SYSTEM'
    }

    def __init__(
        self,
        token: Secret = Secret.from_env_var(['COHERE_API_KEY', 'CO_API_KEY']),
        base_url: str = 'https://api.cohere.com',
        timeout: float | None = None,
        model: str = 'command',
        stream: bool = False,
        streaming_callback: StreamingCallback | None = None,
        generation_args: dict[str, Any] | None = None
    ):
        super().__init__()
        self.model = model
        self.stream = stream
        self.streaming_callback = streaming_callback
        self.generation_args = generation_args or {}
        self.client = cohere.Client(
            api_key=token.resolve_value(),
            base_url=base_url,
            client_name='modstack',
            timeout=timeout
        )

    @command(LLMCommand)
    def chat(
        self,
        messages: list[ChatMessage],
        generation_args: dict[str, Any] | None = None,
        **kwargs
    ) -> Iterator[ChatMessage]:
        if not messages:
            yield from []

        generation_args = {**self.generation_args, **(generation_args or {})}
        chat_history = [
            self._build_cohere_message(message)
            for message in messages[:-1]
        ]
        if self.stream:
            response = self.client.chat_stream(
                message=messages[-1].content,
                chat_history=chat_history,
                model=self.model,
                **generation_args
            )

            text = ''
            finish_response: cohere.NonStreamedChatResponse | None = None
            for event in response:
                if self.streaming_callback:
                    self.streaming_callback(
                        event.text,
                        {'event_type': event.event_type, **(event.response.meta or {})}
                    )
                if event.event_type == 'llm-generation':
                    text += event.text
                elif event.event_type == 'stream-end':
                    finish_response = event.response

            chat_message = ChatMessage.from_assistant(text)
            self._build_metadata(chat_message.metadata, finish_response)
            yield chat_message
        else:
            response = self.client.chat(
                message=messages[-1].content,
                chat_history=chat_history,
                model=self.model,
                **generation_args
            )
            chat_message = ChatMessage.from_assistant(response.text)
            self._build_metadata(chat_message.metadata, response)
            yield chat_message

    def _build_cohere_message(self, message: ChatMessage) -> cohere.ChatMessage:
        return cohere.ChatMessage(
            role=self.ROLES_MAP[message.role],
            message=message.content
        )

    def _build_metadata(self, metadata: dict[str, Any], response: cohere.NonStreamedChatResponse) -> None:
        metadata['model'] = self.model
        build_cohore_metadata(metadata, response)