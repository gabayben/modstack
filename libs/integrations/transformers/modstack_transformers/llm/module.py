from typing import Iterable

from modstack.auth import Secret
from modstack.contracts import CallLLM
from modstack.modules import Modules
from modstack.typing import ChatMessage
from modstack_huggingface import HFTextGenerationTask

class HuggingFaceLocalLLM(Modules.Sync[CallLLM, Iterable[ChatMessage]]):
    def __init__(
        self,
        model: str,
        task: HFTextGenerationTask | None = None,
        token: Secret | None = Secret.from_env_var('HF_API_TOKEN', strict=False)
    ):
        pass

    def _invoke(self, data: CallLLM) -> Iterable[ChatMessage]:
        pass