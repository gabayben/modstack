from typing import Any, Type

from pydantic import BaseModel, Field

from modstack.typing import Serializable

class ToolDef(Serializable):
    name: str
    description: str
    args_schema: Type[BaseModel]
    result_schema: Type[BaseModel]
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __init__(
        self,
        name: str,
        description: str,
        args_schema: Type[BaseModel],
        result_schema: Type[BaseModel],
        metadata: dict[str, Any] = {},
        **kwargs
    ):
        super().__init__(
            name=name,
            description=description,
            args_schema=args_schema,
            result_schema=result_schema,
            metadata=metadata,
            **kwargs
        )

class ToolResult(Serializable):
    tool: str
    result: Any | None

    def __init__(
        self,
        tool: str,
        result: Any | None,
        **kwargs
    ):
        super().__init__(
            tool=tool,
            result=result,
            **kwargs
        )