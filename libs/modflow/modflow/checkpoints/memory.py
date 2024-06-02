"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/checkpoints/memory.py
"""

from collections import defaultdict
from typing import Any, AsyncIterator, Iterator, Optional

from modflow.checkpoints import Checkpoint, CheckpointMetadata, CheckpointTuple, Checkpointer
from modflow.serde import SerializerProtocol

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
    ) -> Iterator[CheckpointTuple]:
        pass

    async def asearch(
        self,
        metadata: CheckpointMetadata,
        *,
        limit: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[CheckpointTuple]:
        pass

    def get_list(self, limit: Optional[int] = None, **kwargs) -> Iterator[CheckpointTuple]:
        pass

    async def aget_list(self, limit: Optional[int] = None, **kwargs) -> AsyncIterator[CheckpointTuple]:
        pass

    def get(self, **kwargs) -> Optional[CheckpointTuple]:
        pass

    async def aget(self, **kwargs) -> Optional[CheckpointTuple]:
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