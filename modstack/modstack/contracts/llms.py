from typing import Iterable

from modstack.contracts import ToolDef, ToolResult
from modstack.typing import ChatMessage, ChatRole, Serializable

class LLMRequest(Serializable):
    prompt: str
    role: ChatRole | None = None
    history: Iterable[ChatMessage] | None = None

    def __init__(
        self,
        prompt: str,
        role: ChatRole | None = None,
        history: Iterable[ChatMessage] | None = None,
        **kwargs
    ):
        super().__init__(
            prompt=prompt,
            role=role,
            history=history,
            **kwargs
        )

class AgenticLLMRequest(LLMRequest):
    tools: list[ToolDef] | None = None
    tool_results: list[ToolResult] | None = None

    def __init__(
        self,
        prompt: str,
        role: ChatRole | None = None,
        history: Iterable[ChatMessage] | None = None,
        tools: list[ToolDef] | None = None,
        tool_results: list[ToolResult] | None = None,
        **kwargs
    ):
        super().__init__(
            prompt=prompt,
            role=role,
            history=history,
            tools=tools,
            tool_results=tool_results,
            **kwargs
        )