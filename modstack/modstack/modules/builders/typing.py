from typing import Any

from modstack.typing import Serializable

class DynamicPromptData(Serializable):
    prompt_source: str
    template_variables: dict[str, Any] | None = None