from typing import Iterator

from modstack.core.auth import Secret
from modstack.core.modules import Modules
from modstack.core.modules.ai import LLMRequest
from modstack.core.typing.messages import ChatMessageChunk
from modstack.huggingface import HFTextGenerationTask

class HuggingFaceLocalLLM(Modules.Stream[LLMRequest, list[ChatMessageChunk]]):
    def __init__(
        self,
        model: str,
        task: HFTextGenerationTask | None = None,
        token: Secret | None = Secret.from_env_var('HF_API_TOKEN', strict=False)
    ):
        pass

    def _iter(self, data: LLMRequest, **kwargs) -> Iterator[list[ChatMessageChunk]]:
        pass