from typing import Iterator

from modstack.auth import Secret
from modstack.core import Modules
from modstack.modules import LLMPrompt
from modstack.artifacts.messages import MessageChunk
from modstack.huggingface import HFTextGenerationTask

class HuggingFaceLocalLLM(Modules.Stream[LLMPrompt, MessageChunk]):
    def __init__(
        self,
        model: str,
        task: HFTextGenerationTask | None = None,
        token: Secret | None = Secret.from_env_var('HF_API_TOKEN', strict=False)
    ):
        pass

    def _iter(self, data: LLMPrompt, **kwargs) -> Iterator[MessageChunk]:
        pass