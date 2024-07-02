from typing import Optional

from llama_cpp import ChatCompletionRequestMessage, Llama

from modstack.core import Modules
from modstack.artifacts.messages import MessageArtifact, MessageChunk, MessageType
from modstack.modules import LLMPrompt

class LlamaCppLLM(Modules.Sync[LLMPrompt, MessageChunk]):
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
        prompt: LLMPrompt,
        role: MessageType = MessageType.HUMAN,
        echo: bool = False,
        **kwargs
    ) -> MessageChunk:
        response = self.client.create_chat_completion(
            _convert_to_llamacpp_messages(prompt.messages)
        )

def _convert_to_llamacpp_messages(messages: list[MessageArtifact]) -> list[ChatCompletionRequestMessage]:
    formatted_messages: list[ChatCompletionRequestMessage] = []
    for message in messages:
        formatted_messages.append({
            'content': message.content,
            'role': message.message_type,
            'name': message.name
        })
    return formatted_messages