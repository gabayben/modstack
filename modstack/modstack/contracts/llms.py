from typing import Iterable

from modstack.typing import ChatMessage, ChatRole, Serializable, Tool, ToolResult

class LLMRequest(Serializable):
    prompt: str
    role: ChatRole | None = None
    history: Iterable[ChatMessage] | None = None
    tools: list[Tool] | None = None
    tool_results: list[ToolResult] | None = None

    def __init__(
        self,
        prompt: str,
        role: ChatRole | None = None,
        history: Iterable[ChatMessage] | None = None,
        tools: list[Tool] | None = None,
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