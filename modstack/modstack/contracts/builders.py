from typing import Any

from modstack.contracts import Contract

class BuildPrompt(Contract):
    pass

class BuildDynamicPrompt(Contract):
    prompt_source: str
    template_variables: dict[str, Any] | None = None