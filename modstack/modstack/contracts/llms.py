from typing import Any, Iterable

from modstack.contracts import Contract
from modstack.typing import ChatMessage, ChatRole, Tool, ToolResult

class CallLLM(Contract[Iterable[ChatMessage]]):
    prompt: str
    role: ChatRole | None = None
    history: Iterable[ChatMessage] | None = None
    tools: list[Tool] | None = None
    tool_results: list[ToolResult] | None = None
    generation_args: dict[str, Any] | None = None

    def __init__(
        self,
        prompt: str,
        role: ChatRole | None = None,
        history: Iterable[ChatMessage] | None = None,
        tools: list[Tool] | None = None,
        tool_results: list[ToolResult] | None = None,
        generation_args: dict[str, Any] | None = None,
        **kwargs
    ):
        super().__init__(
            prompt=prompt,
            role=role,
            history=history,
            tools=tools,
            tool_results=tool_results,
            generation_args=generation_args,
            **kwargs
        )

    @classmethod
    def name(cls) -> str:
        return 'call_llm'