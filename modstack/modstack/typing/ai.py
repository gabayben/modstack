from typing import Any, NotRequired, TypedDict

class ToolCall(TypedDict):
    name: str
    args: dict[str, Any]
    id: NotRequired[str]

class ToolCallChunk(TypedDict):
    name: NotRequired[str]
    args: NotRequired[str]
    id: NotRequired[str]
    index: NotRequired[int]

class InvalidToolCall(TypedDict):
    name: NotRequired[str]
    args: NotRequired[str]
    id: NotRequired[str]
    error: NotRequired[str]

class UsageMetadata(TypedDict):
    input_tokens: int
    output_tokens: int
    total_tokens: int