from typing import Any, Protocol

class SerializerProtocol(Protocol):
    def dumps(self, obj: Any) -> bytes:
        pass

    def loads(self, data: bytes) -> Any:
        pass