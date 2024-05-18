from typing import Any, Iterable

from modstack.contracts import Contract
from modstack.typing import ChatMessage

class CallAgent(Contract[Iterable[ChatMessage]]):
    messages: Iterable[ChatMessage]
    generation_args: dict[str, Any] | None = None