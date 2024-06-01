from modstack.core.modules.ai import AgenticLLMRequest

class LlamaCppLLMRequest(AgenticLLMRequest):
    echo: bool = False