from typing import Any, ClassVar

import cohere

from modstack.auth import Secret
from modstack.contracts import AgenticLLMRequest, ToolSpec, ToolResult
from modstack.modules import Modules
from modstack.typing.messages import ChatMessage, ChatMessageChunk, ChatRole
from modstack_cohere.utils import build_cohore_metadata

class CohereLLM(Modules.Stream[AgenticLLMRequest, ChatMessageChunk]):
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

    def _iter(self, data: AgenticLLMRequest, **kwargs) -> ChatMessageChunk:
        generation_args = {**self.generation_args, **(data.model_extra or {})}
        chat_history = [
            self._build_cohere_message(message)
            for message in data.history
        ] if data.history else []
        cohere_tools: list[cohere.Tool] = self._build_cohere_tools(data.tools) if data.tools else None
        cohere_tool_results: list[cohere.ToolResult] = self._build_cohere_tool_results(data.tool_results) if data.tool_results else None

        response = self.client.chat_stream(
            message=data.prompt,
            chat_history=chat_history,
            tools=cohere_tools,
            tool_results=cohere_tool_results,
            model=self.model,
            **generation_args
        )

        for event in response:
            chat_message = ChatMessageChunk(event.text, ChatRole.ASSISTANT)
            if event.event_type == 'llm-generation':
                chat_message.metadata.update({
                    'event_type': event.event_type,
                    **(event.response.meta or {})
                })
            elif event.event_type == 'stream-end':
                self._build_metadata(chat_message.metadata, response)
            yield chat_message

    def _build_cohere_message(self, message: ChatMessage) -> cohere.ChatMessage:
        return cohere.ChatMessage(
            role=self.ROLES_MAP[message.role],
            message=message.content
        )

    def _build_cohere_tools(self, tools: list[ToolSpec]) -> list[cohere.Tool]:
        return []

    def _build_cohere_tool_results(self, tool_results: list[ToolResult]) -> list[cohere.ToolResult]:
        return []

    def _build_metadata(self, metadata: dict[str, Any], response: cohere.StreamedChatResponse | cohere.NonStreamedChatResponse) -> None:
        metadata['model'] = self.model
        build_cohore_metadata(metadata, response)