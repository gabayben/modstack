from typing import override

from modstack.contracts import LLMCall

class AnthropicLLMCall(LLMCall):
    max_tokens: int | None = None
    system_prompt: str | None = None
    top_k: int | None = None
    top_p: float | None = None
    temperature: float | None = None
    stop_sequences: list[str] | None = None
    stream: bool = False

    @classmethod
    @override
    def name(cls) -> str:
        return 'anthropic_llm_call'