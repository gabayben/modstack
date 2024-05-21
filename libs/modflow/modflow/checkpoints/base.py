from abc import ABC, abstractmethod
from collections import defaultdict
from enum import StrEnum
from typing import Any, Protocol, TypedDict

from modstack.typing import Effect

class Checkpoint(TypedDict):
    """
    Taken from LangGraph's Checkpoint.
    """

    """
    The version of the checkpoint format. Currently 1.
    """
    version: int

    """
    The timestamp of the checkpoint in ISO 8601 format.
    """
    timestamp: str

    """
    The versions of the channels at the time of the checkpoint.
    The keys are channel names and the values are the logical time step
    at which the channel was last updated.
    """
    channel_versions: defaultdict[str, int]

    """
    Map from node ID to map from channel name to version seen.
    This keeps track of the versions of the channels that each node has seen.
    Used to determine which nodes to execute next.
    """
    versions_seen: defaultdict[str, defaultdict[str, int]]

    """
    The values of the channels at the time of the checkpoint.
    Mapping from channel name to channel snapshot value.
    """
    channel_values: dict[str, Any]

class CheckpointAt(StrEnum):
    """
    Taken from LangGraph's CheckpointAt.
    """

    END_OF_STEP = 'end_of_step'
    END_OF_RUN = 'end_of_run'

class CheckpointSerializer(Protocol):
    """
    Taken from LangGraph's CheckpointSerializer.
    """

    def loads(self, bytes_: bytes) -> Any:
        pass

    def dumps(self, data: Any) -> bytes:
        pass

class Checkpointer(ABC):
    """
    Mostly taken from LangGraph's CheckpointSaver.
    """

    at: CheckpointAt = CheckpointAt.END_OF_STEP
    serde: CheckpointSerializer

    def __init__(
        self,
        at: CheckpointAt | None = None,
        serde: CheckpointSerializer | None = None
    ):
        self.at = at or self.at
        self.serde = serde or self.serde

    @abstractmethod
    def get(self, **kwargs) -> Effect[Checkpoint | None]:
        pass

    @abstractmethod
    def put(self, checkpoint: Checkpoint, **kwargs) -> Effect[None]:
        pass