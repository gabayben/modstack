from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Mapping

from uuid6 import uuid6

from modflow.channels import Channel, EmptyChannelError
from modflow.checkpoints import Checkpoint

def _seen_dict() -> defaultdict[str, int]:
    return defaultdict(int)

def empty_checkpoint() -> Checkpoint:
    return Checkpoint(
        id=str(uuid6(clock_seq=-2)),
        version=1,
        timestamp=datetime.now(timezone.utc).isoformat(),
        channel_versions=defaultdict(int),
        versions_seen=defaultdict(_seen_dict),
        channel_values={}
    )

def copy_checkpoint(checkpoint: Checkpoint) -> Checkpoint:
    return Checkpoint(
        id=checkpoint['id'],
        version=checkpoint['version'],
        timestamp=checkpoint['timestamp'],
        channel_versions=checkpoint['channel_versions'].copy(),
        versions_seen=defaultdict(
            _seen_dict,
            {k: defaultdict(int, v) for k, v in checkpoint["versions_seen"].items()},
        ),
        channel_values=checkpoint['channel_values'].copy()
    )

def create_checkpoint(checkpoint: Checkpoint, channels: Mapping[str, Channel], step: int) -> Checkpoint:
    values: dict[str, Any] = {}
    for k, channel in channels.items():
        try:
            values[k] = channel.checkpoint()
        except EmptyChannelError:
            pass
    return Checkpoint(
        id=str(uuid6(clock_seq=step)),
        version=1,
        timestamp=datetime.now(timezone.utc).isoformat(),
        channel_versions=checkpoint['channel_versions'],
        versions_seen=checkpoint['versions_seen'],
        channel_values=values
    )