from typing import Any

from modstack.core.typing import Serializable

class PromptData(Serializable):
    pass

class DynamicPromptData(Serializable):
    prompt_source: str
    template_variables: dict[str, Any] | None = None