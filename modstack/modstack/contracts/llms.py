from typing import Iterable

from modstack.contracts import ToolSpec, ToolResult
from modstack.typing import Serializable
from modstack.typing.messages import ChatMessage, ChatRole

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
    tools: list[ToolSpec] | None = None
    tool_results: list[ToolResult] | None = None

    def __init__(
        self,
        prompt: str,
        role: ChatRole | None = None,
        history: Iterable[ChatMessage] | None = None,
        tools: list[ToolSpec] | None = None,
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