from modstack.contracts import AgenticLLMRequest

class LlamaCppLLMRequest(AgenticLLMRequest):
    echo: bool = False