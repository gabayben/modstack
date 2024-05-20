from typing import Any, Iterable

from huggingface_hub import ChatCompletionOutput, ChatCompletionStreamOutput, InferenceClient

from modstack.auth import Secret
from modstack.endpoints import endpoint
from modstack.modules import Module
from modstack.typing import ChatMessage, ChatRole, StreamingCallback
from modstack.utils.paths import validate_url
from modstack_hf_hub import HFGenerationApiType, HFModelType
from modstack_hf_hub.utils import validate_hf_model

class HuggingFaceApiLLM(Module):
    def __init__(
        self,
        model_or_url: str,
        api_type: HFGenerationApiType,
        token: Secret | None = Secret.from_env_var('HF_API_TOKEN', strict=False),
        streaming_callback: StreamingCallback | None = None,
        stream: bool = False,
        stop_words: list[str] | None = None,
        max_tokens: int = 512,
        generation_args: dict[str, Any] = {}
    ):
        super().__init__()

        if api_type == HFGenerationApiType.SERVERLESS_INFERENCE_API:
            validate_hf_model(model_or_url, HFModelType.GENERATION, token)
        else:
            validate_url(model_or_url)

        self.generation_args = generation_args
        self.generation_args['stop'] = self.generation_args.get('stop', [])
        self.generation_args['stop'].extend(stop_words or [])
        self.generation_args.setdefault('max_tokens', max_tokens)
        self.generation_args.setdefault('stream', stream)
        self.streaming_callback = streaming_callback
        self.client = InferenceClient(model_or_url, token=token.resolve_value() if token else None)

    @endpoint
    def effect(
        self,
        prompt: str,
        role: ChatRole | None = None,
        history: Iterable[ChatMessage] | None = None,
        generation_args: dict[str, Any] | None = None,
        **kwargs
    ) -> Iterable[ChatMessage]:
        generation_args = {**self.generation_args, **(generation_args or {})}
        history = history or []
        history.append(ChatMessage(prompt, role or ChatRole.USER))
        messages = [message.to_common_format() for message in history]

        if generation_args.get('stream'):
            chunks: Iterable[ChatCompletionStreamOutput] = self.client.chat_completion(
                messages,
                stream=True,
                **generation_args
            )

            generated_text = ''
            for chunk in chunks:
                text = chunk.choices[0].delta.content
                if text:
                    generated_text += text
                metadata = {}
                finish_reason = chunk.choices[0].finish_reason
                if finish_reason:
                    metadata['finish_reason'] = finish_reason
                if self.streaming_callback:
                    self.streaming_callback(text, metadata)

            message = ChatMessage.from_assistant(generated_text)
            message.metadata.update({'model': self.client.model, 'finish_reason': finish_reason, 'index': 0})
            return [message]
        else:
            output: ChatCompletionOutput = self.client.chat_completion(
                messages,
                stream=False,
                **generation_args
            )

            results: list[ChatMessage] = []
            for choice in output.choices:
                message = ChatMessage.from_assistant(choice.message.content)
                message.metadata.update({'model': self.client.model, 'finish_reason': choice.finish_reason, 'index': choice.index})
                results.append(message)
            return results