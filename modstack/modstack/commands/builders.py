from typing import Any

from modstack.commands import Command

class BuildPrompt(Command[str]):
    @classmethod
    def name(cls) -> str:
        return 'build_prompt'

class BuildDynamicPrompt(Command[str]):
    prompt_source: str
    template_variables: dict[str, Any] | None = None

    @classmethod
    def name(cls) -> str:
        return 'build_dynamic_prompt'