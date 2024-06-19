from typing import Optional

from llama_cpp import ChatCompletionRequestMessage, Llama

from modstack.modules import Modules
from modstack.artifacts.messages import ChatMessageChunk, ChatRole
from modstack.modules.ai import AgenticLLMRequest

class LlamaCppLLM(Modules.Sync[AgenticLLMRequest, ChatMessageChunk]):
    def __init__(
        self,
        model: str,
        chat_format: Optional[str] = None
    ):
        self.client = Llama(
            model,
            chat_format=chat_format
        )

    def _invoke(
        self,
        data: AgenticLLMRequest,
        role: ChatRole = ChatRole.USER,
        echo: bool = False,
        **kwargs
    ) -> ChatMessageChunk:
        history = data.history or []
        history.append(ChatMessageChunk(
            data.prompt,
            role or ChatRole.USER
        ))

        response = self.client.create_chat_completion(
            _convert_to_llamacpp_messages(history),
            **data.model_dump(
                exclude={'prompt', 'history', 'tools', 'tool_results'},
                exclude_unset=True
            )
        )

def _convert_to_llamacpp_messages(messages: list[ChatMessageChunk]) -> list[ChatCompletionRequestMessage]:
    formatted_messages: list[ChatCompletionRequestMessage] = []
    for message in messages:
        formatted_messages.append({
            'content': message.content,
            'role': message.role,
            'name': message.name
        })
    return formatted_messages