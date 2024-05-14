from typing import override

from modstack.commands import LLMCommand

class OllamaLLMCommand(LLMCommand):
    images: list[str] | None = None
    system_prompt: str | None = None
    template: str | None = None
    timeout: int | None = None
    raw: bool | None = None

    @classmethod
    @override
    def name(cls) -> str:
        return 'ollama_llm_command'