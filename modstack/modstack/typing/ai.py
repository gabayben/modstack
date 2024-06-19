from typing import Any, NotRequired, Optional, TypedDict

class ToolCall(TypedDict):
    name: str
    args: dict[str, Any]
    id: NotRequired[Optional[str]]

class ToolCallChunk(TypedDict):
    name: NotRequired[Optional[str]]
    args: NotRequired[Optional[str]]
    id: NotRequired[Optional[str]]
    index: NotRequired[Optional[int]]

class InvalidToolCall(TypedDict):
    name: NotRequired[Optional[str]]
    args: NotRequired[Optional[str]]
    id: NotRequired[Optional[str]]
    error: NotRequired[Optional[str]]

class UsageMetadata(TypedDict):
    input_tokens: int
    output_tokens: int
    total_tokens: int