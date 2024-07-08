from typing import Any, ClassVar, Iterator

import cohere

from modstack.cohere.utils import build_cohore_metadata
from modstack.artifacts.messages import AiMessageChunk, MessageArtifact, MessageChunk, MessageType
from modstack.config import Secret
from modstack.core import Modules
from modstack.ai import LLMPrompt

class CohereLLM(Modules.Stream[LLMPrompt, MessageChunk]):
    ROLES_MAP: ClassVar[dict[MessageType, str]] = {
        MessageType.HUMAN: 'USER',
        MessageType.FUNCTION: 'USER',
        MessageType.AI: 'CHAT',
        MessageType.SYSTEM: 'SYSTEM'
    }

    def __init__(
        self,
        token: Secret = Secret.from_env_var(['COHERE_API_KEY', 'CO_API_KEY']),
        base_url: str = 'https://api.cohere.com',
        timeout: float | None = None,
        model: str = 'command',
        generation_args: dict[str, Any] | None = None
    ):
        super().__init__()
        self.model = model
        self.generation_args = generation_args or {}
        self.client = cohere.Client(
            api_key=token.resolve_value(),
            base_url=base_url,
            client_name='modstack',
            timeout=timeout
        )

    def _stream(
        self,
        prompt: LLMPrompt,
        role: MessageType = MessageType.HUMAN,
        **kwargs
    ) -> Iterator[MessageChunk]:
        generation_args = {**self.generation_args, **kwargs}
        chat_history = [
            self._build_cohere_message(message)
            for message in prompt.history
        ]

        response = self.client.chat_stream(
            message=str(prompt.prompt),
            chat_history=chat_history,
            model=self.model,
            **generation_args
        )

        for event in response:
            chat_message = AiMessageChunk(event.text or '')
            if event.event_type == 'llm-generation':
                chat_message.metadata.update({
                    'event_type': event.event_type,
                    **(event.response.meta or {})
                })
            elif event.event_type == 'stream-end':
                chat_message.metadata['model'] = self.model
                build_cohore_metadata(chat_message.metadata, response)
            yield chat_message

    def _build_cohere_message(self, message: MessageArtifact) -> cohere.Message:
        return cohere.Message(
            role=self.ROLES_MAP[message.message_type],
            message=message.content
        )