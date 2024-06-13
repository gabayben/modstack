from typing import Iterable

from modstack.modules.tools import ToolResult, ToolSpec
from modstack.typing import Schema
from modstack.artifacts.messages import ChatMessage

class LLMRequest(Schema):
    prompt: str
    history: Iterable[ChatMessage] | None = None

    def __init__(
        self,
        prompt: str,
        history: Iterable[ChatMessage] | None = None,
        **kwargs
    ):
        super().__init__(
            prompt=prompt,
            history=history,
            **kwargs
        )

class AgenticLLMRequest(LLMRequest):
    tools: list[ToolSpec] | None = None
    tool_results: list[ToolResult] | None = None

    def __init__(
        self,
        prompt: str,
        history: Iterable[ChatMessage] | None = None,
        tools: list[ToolSpec] | None = None,
        tool_results: list[ToolResult] | None = None,
        **kwargs
    ):
        super().__init__(
            prompt=prompt,
            history=history,
            tools=tools,
            tool_results=tool_results,
            **kwargs
        )