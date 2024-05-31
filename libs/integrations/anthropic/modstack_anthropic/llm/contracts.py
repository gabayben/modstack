from modstack.modules.models import LLMRequest

class AnthropicLLMRequest(LLMRequest):
    max_tokens: int | None = None
    system_prompt: str | None = None
    top_k: int | None = None
    top_p: float | None = None
    temperature: float | None = None
    stop_sequences: list[str] | None = None