from typing import Any, Iterable, Iterator

from huggingface_hub import ChatCompletionStreamOutput, InferenceClient

from modstack.core.auth import Secret
from modstack.core.modules import Modules
from modstack.core.modules.ai import LLMRequest
from modstack.core.typing.messages import ChatMessage, ChatMessageChunk, ChatRole
from modstack.core.utils.paths import validate_url
from modstack.huggingface import HFGenerationApiType, HFModelType
from modstack.huggingface.utils import validate_hf_model

class HuggingFaceApiLLM(Modules.Stream[LLMRequest, list[ChatMessageChunk]]):
    def __init__(
        self,
        model_or_url: str,
        api_type: HFGenerationApiType,
        token: Secret | None = Secret.from_env_var('HF_API_TOKEN', strict=False),
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
        self.client = InferenceClient(model_or_url, token=token.resolve_value() if token else None)

    def _iter(self, data: LLMRequest, **kwargs) -> Iterator[list[ChatMessageChunk]]:
        generation_args = {**self.generation_args, **(data.model_extra or {})}
        history = data.history or []
        history.append(ChatMessage(data.prompt, data.role or ChatRole.USER))
        messages = [message.to_common_format() for message in history]

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
            yield [ChatMessageChunk(text, ChatRole.ASSISTANT, metadata=metadata)]