from modstack.auth import Secret
from modstack.contracts import LLMRequest
from modstack.modules import Modules
from modstack.typing.messages import ChatMessage
from modstack_huggingface import HFTextGenerationTask

class HuggingFaceLocalLLM(Modules.Sync[LLMRequest, list[ChatMessage]]):
    def __init__(
        self,
        model: str,
        task: HFTextGenerationTask | None = None,
        token: Secret | None = Secret.from_env_var('HF_API_TOKEN', strict=False)
    ):
        pass

    def _invoke(self, data: LLMRequest, **kwargs) -> list[ChatMessage]:
        pass