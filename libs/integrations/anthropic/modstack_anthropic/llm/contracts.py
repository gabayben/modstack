from modstack.contracts import CallLLM

class CallAnthropicLLM(CallLLM):
    max_tokens: int | None = None
    system_prompt: str | None = None
    top_k: int | None = None
    top_p: float | None = None
    temperature: float | None = None
    stop_sequences: list[str] | None = None
    stream: bool = False