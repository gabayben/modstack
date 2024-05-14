from typing import Any

from modstack.contracts import Contract

class BuildPrompt(Contract[str]):
    @classmethod
    def name(cls) -> str:
        return 'build_prompt'

class BuildDynamicPrompt(Contract[str]):
    prompt_source: str
    template_variables: dict[str, Any] | None = None

    @classmethod
    def name(cls) -> str:
        return 'build_dynamic_prompt'