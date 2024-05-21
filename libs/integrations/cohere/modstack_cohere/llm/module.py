from typing import Any, ClassVar, Iterable

import cohere

from modstack.auth import Secret
from modstack.contracts import AgenticLLMRequest, ToolSpec, ToolResult
from modstack.modules import Modules
from modstack.typing import ChatMessage, ChatRole, StreamingCallback
from modstack_cohere.utils import build_cohore_metadata

class CohereLLM(Modules.Sync[AgenticLLMRequest, Iterable[ChatMessage]]):
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

    def _invoke(self, data: AgenticLLMRequest, **kwargs) -> Iterable[ChatMessage]:
        generation_args = {**self.generation_args, **(data.model_extra or {})}
        chat_history = [
            self._build_cohere_message(message)
            for message in data.history
        ] if data.history else []
        cohere_tools: list[cohere.Tool] = self._build_cohere_tools(data.tools) if data.tools else None
        cohere_tool_results: list[cohere.ToolResult] = self._build_cohere_tool_results(data.tool_results) if data.tool_results else None

        if self.stream:
            response = self.client.chat_stream(
                message=data.prompt,
                chat_history=chat_history,
                tools=cohere_tools,
                tool_results=cohere_tool_results,
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
            return [chat_message]
        else:
            response = self.client.chat(
                message=data.prompt,
                chat_history=chat_history,
                tools=cohere_tools,
                tool_results=cohere_tool_results,
                model=self.model,
                **generation_args
            )
            chat_message = ChatMessage.from_assistant(response.text)
            self._build_metadata(chat_message.metadata, response)
            return [chat_message]

    def _build_cohere_message(self, message: ChatMessage) -> cohere.ChatMessage:
        return cohere.ChatMessage(
            role=self.ROLES_MAP[message.role],
            message=message.content
        )

    def _build_cohere_tools(self, tools: list[ToolSpec]) -> list[cohere.Tool]:
        pass

    def _build_cohere_tool_results(self, tool_results: list[ToolResult]) -> list[cohere.ToolResult]:
        pass

    def _build_metadata(self, metadata: dict[str, Any], response: cohere.NonStreamedChatResponse) -> None:
        metadata['model'] = self.model
        build_cohore_metadata(metadata, response)