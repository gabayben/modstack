from typing import Any, Optional

from modstack.artifacts import Artifact
from modstack.config import EnvVarSecret, Secret
from modstack.core import Modules

class HuggingFaceApiTextEmbedder(Modules.Sync[list[Artifact], list[Artifact]]):
    def __init__(
        self,
        model_or_url: str = 'intfloat/multilingual-e5-large-instruct',
        token: Optional[Secret] = EnvVarSecret.from_env_var('HF_API_TOKEN', strict=False),
        generation_args: dict[str, Any] = {},
        **kwargs
    ):
        super().__init__(**kwargs)

    def _invoke(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        pass