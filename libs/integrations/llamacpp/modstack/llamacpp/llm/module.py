from typing import Optional

from llama_cpp import ChatCompletionRequestMessage, Llama

from modstack.modules import Modules
from modstack.artifacts.messages import HumanMessageChunk, MessageChunk, MessageType
from modstack.modules.ai import LLMRequest

class LlamaCppLLM(Modules.Sync[LLMRequest, MessageChunk]):
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
        data: LLMRequest,
        role: MessageType = MessageType.HUMAN,
        echo: bool = False,
        **kwargs
    ) -> MessageChunk:
        history = data.messages or []
        history.append(HumanMessageChunk(
            str(data.prompt),
            role=role
        ))

        response = self.client.create_chat_completion(
            _convert_to_llamacpp_messages(history),
            **data.model_dump(
                exclude={'prompt', 'history', 'tools', 'tool_results'},
                exclude_unset=True
            )
        )

def _convert_to_llamacpp_messages(messages: list[MessageChunk]) -> list[ChatCompletionRequestMessage]:
    formatted_messages: list[ChatCompletionRequestMessage] = []
    for message in messages:
        formatted_messages.append({
            'content': message.content,
            'role': message.message_type,
            'name': message.name
        })
    return formatted_messages