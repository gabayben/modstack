from typing import Any

from modstack.commands import Command

class BuildPrompt(Command[str]):
    pass

class BuildDynamicPrompt(Command[str]):
    prompt_source: str
    template_variables: dict[str, Any] | None = None