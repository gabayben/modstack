from typing import override

from modstack.commands import CallLLM

class CallAnthropicLLM(CallLLM):
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
        return 'call_anthropic_llm'