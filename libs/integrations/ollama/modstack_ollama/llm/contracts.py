from modstack.modules.models import LLMRequest

class OllamaLLMRequest(LLMRequest):
    images: list[str] | None = None
    system_prompt: str | None = None
    template: str | None = None
    timeout: int | None = None
    raw: bool | None = None
    stream: bool | None = None