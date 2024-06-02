"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/checkpoints/memory.py
"""

from collections import defaultdict
from typing import Any, Optional

from modflow.checkpoints import Checkpoint, CheckpointMetadata, CheckpointTuple, Checkpointer
from modflow.serde import SerializerProtocol
from modstack.core.typing import Effect

class MemoryCheckpointer(Checkpointer):
    """
    An in-memory checkpointer.

    This checkpointer stores checkpoints in memory using a defaultdict.

    Note:
        Since checkpoints are saved in memory, they will be lost when the program exits.
        Only use this checkpointer for debugging or testing purposes.

    Args:
        serde (Optional[SerializerProtocol]): The serializer to use for serializing and deserializing checkpoints. Defaults to None.
    """

    storage: dict[str, dict[str, tuple[bytes, bytes]]]

    def __init__(
        self,
        *,
        serde: SerializerProtocol | None = None
    ):
        super().__init__(serde=serde)
        self.storage = defaultdict(dict)

    def search(
        self,
        metadata: CheckpointMetadata,
        *,
        limit: Optional[int] = None,
        **kwargs
    ) -> Effect[CheckpointTuple | None]:
        pass

    def get(self, **kwargs) -> Effect[CheckpointTuple | None]:
        pass

    def put(
        self,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        **kwargs
    ) -> dict[str, Any]:
        pass

    async def aput(
        self,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        **kwargs
    ) -> dict[str, Any]:
        pass