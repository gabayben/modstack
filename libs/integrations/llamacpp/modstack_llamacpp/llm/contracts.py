from modstack.modules.models import AgenticLLMRequest

class LlamaCppLLMRequest(AgenticLLMRequest):
    echo: bool = False