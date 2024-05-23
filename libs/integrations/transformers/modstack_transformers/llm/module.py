from typing import Iterator

from modstack.auth import Secret
from modstack.contracts import LLMRequest
from modstack.modules import Modules
from modstack.typing.messages import ChatMessageChunk
from modstack_huggingface import HFTextGenerationTask

class HuggingFaceLocalLLM(Modules.Stream[LLMRequest, ChatMessageChunk]):
    def __init__(
        self,
        model: str,
        task: HFTextGenerationTask | None = None,
        token: Secret | None = Secret.from_env_var('HF_API_TOKEN', strict=False)
    ):
        pass

    def _iter(self, data: LLMRequest, **kwargs) -> Iterator[ChatMessageChunk]:
        pass