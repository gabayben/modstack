from typing import Any, Iterable, Iterator

from huggingface_hub import ChatCompletionStreamOutput, InferenceClient

from modstack.config import Secret
from modstack.core import Modules
from modstack.ai import LLMPrompt
from modstack.artifacts.messages import AiMessageChunk, MessageChunk, MessageType
from modstack.utils.paths import validate_url
from modstack.huggingface import HFGenerationApiType, HFModelType
from modstack.huggingface.utils import validate_hf_model

class HuggingFaceApiLLM(Modules.Stream[LLMPrompt, MessageChunk]):
    def __init__(
        self,
        model_or_url: str,
        api_type: HFGenerationApiType,
        token: Secret | None = Secret.from_env_var('HF_API_TOKEN', strict=False),
        stop_words: list[str] | None = None,
        max_tokens: int = 512,
        generation_args: dict[str, Any] = {},
        **kwargs
    ):
        super().__init__(**kwargs)

        if api_type == HFGenerationApiType.SERVERLESS_INFERENCE_API:
            validate_hf_model(model_or_url, HFModelType.GENERATION, token)
        else:
            validate_url(model_or_url)

        self.generation_args = generation_args
        self.generation_args['stop'] = self.generation_args.get('stop', [])
        self.generation_args['stop'].extend(stop_words or [])
        self.generation_args.setdefault('max_tokens', max_tokens)
        self.client = InferenceClient(model_or_url, token=token.resolve_value() if token else None)

    def _stream(
        self,
        prompt: LLMPrompt,
        role: MessageType = MessageType.HUMAN,
        **kwargs
    ) -> Iterator[MessageChunk]:
        generation_args = {**self.generation_args, **kwargs}
        messages = [message.to_common_format() for message in prompt.messages]

        chunks: Iterable[ChatCompletionStreamOutput] = self.client.chat_completion(
            messages,
            stream=True,
            **generation_args
        )

        for chunk in chunks:
            text = chunk.choices[0].delta.content or ''
            metadata = {}
            finish_reason = chunk.choices[0].finish_reason
            if finish_reason:
                metadata['finish_reason'] = finish_reason
            yield AiMessageChunk(text, metadata=metadata)