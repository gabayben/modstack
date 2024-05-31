from typing import Optional

from llama_cpp import ChatCompletionRequestMessage, Llama

from modstack.modules import Modules
from modstack.typing.messages import ChatMessageChunk, ChatRole
from modstack_llamacpp.llm import LlamaCppLLMRequest

class LlamaCppLLM(Modules.Sync[LlamaCppLLMRequest, list[ChatMessageChunk]]):
    def __init__(
        self,
        model: str,
        chat_format: Optional[str] = None
    ):
        self.client = Llama(
            model,
            chat_format=chat_format
        )

    def _invoke(self, data: LlamaCppLLMRequest, **kwargs) -> list[ChatMessageChunk]:
        history = data.history or []
        history.append(ChatMessageChunk(
            data.prompt,
            data.role or ChatRole.USER
        ))

        response = self.client.create_chat_completion(
            _convert_to_llamacpp_messages(history),
            **data.model_dump(
                exclude={'prompt', 'history', 'role', 'tools', 'tool_results'},
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