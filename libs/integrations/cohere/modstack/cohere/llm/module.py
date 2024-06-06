from typing import Any, ClassVar, Iterator

import cohere

from modstack.cohere.utils import build_cohore_metadata
from modstack.artifacts.messages import ChatMessage, ChatMessageChunk, ChatRole
from modstack.auth import Secret
from modstack.modules import Modules
from modstack.modules.ai import AgenticLLMRequest
from modstack.modules.tools import ToolResult, ToolSpec

class CohereLLM(Modules.Stream[AgenticLLMRequest, list[ChatMessageChunk]]):
    ROLES_MAP: ClassVar[dict[ChatRole, str]] = {
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

    def _iter(self, data: AgenticLLMRequest, **kwargs) -> Iterator[list[ChatMessageChunk]]:
        generation_args = {**self.generation_args, **(data.model_extra or {})}
        chat_history = [
            self._build_cohere_message(message)
            for message in data.history
        ] if data.history else []
        cohere_tools: list[cohere.Tool] = self._build_cohere_tools(data.tools) if data.tools else None
        cohere_tool_results: list[ToolResult] = self._build_cohere_tool_results(data.tool_results) if data.tool_results else None

        response = self.client.chat_stream(
            message=data.prompt,
            chat_history=chat_history,
            tools=cohere_tools,
            tool_results=cohere_tool_results,
            model=self.model,
            **generation_args
        )

        for event in response:
            chat_message = ChatMessageChunk(event.text or '', ChatRole.ASSISTANT)
            if event.event_type == 'llm-generation':
                chat_message.metadata.update({
                    'event_type': event.event_type,
                    **(event.response.meta or {})
                })
            elif event.event_type == 'stream-end':
                chat_message.metadata['model'] = self.model
                build_cohore_metadata(chat_message.metadata, response)
            yield [chat_message]

    def _build_cohere_message(self, message: ChatMessage) -> cohere.ChatMessage:
        return cohere.ChatMessage(
            role=self.ROLES_MAP[message.role],
            message=message.content
        )

    def _build_cohere_tools(self, tools: list[ToolSpec]) -> list[cohere.Tool]:
        return []

    def _build_cohere_tool_results(self, tool_results: list[ToolResult]) -> list[ToolResult]:
        return []