from modstack.contracts import CallLLM

class CallOllamaLLM(CallLLM):
    images: list[str] | None = None
    system_prompt: str | None = None
    template: str | None = None
    timeout: int | None = None
    raw: bool | None = None
    stream: bool | None = None