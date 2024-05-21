from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping

from modflow.channels import Channel, EmptyChannelError
from modflow.checkpoints import Checkpoint

def _seen_dict() -> defaultdict[str, int]:
    return defaultdict(int)

def empty_checkpoint() -> Checkpoint:
    return Checkpoint(
        version=1,
        timestamp=datetime.now(timezone.utc).isoformat(),
        channel_versions=defaultdict(int),
        versions_seen=defaultdict(_seen_dict),
        channel_values={}
    )

def copy_checkpoint(checkpoint: Checkpoint) -> Checkpoint:
    return Checkpoint(
        version=checkpoint['version'],
        timestamp=checkpoint['timestamp'],
        channel_versions=checkpoint['channel_versions'].copy(),
        versions_seen=deepcopy(checkpoint['versions_seen']),
        channel_values=checkpoint['channel_values'].copy()
    )

def create_checkpoint(checkpoint: Checkpoint, channels: Mapping[str, Channel]) -> Checkpoint:
    values: dict[str, Any] = {}
    for k, channel in channels.items():
        try:
            values[k] = channel.checkpoint()
        except EmptyChannelError:
            pass
    return Checkpoint(
        version=1,
        timestamp=datetime.now(timezone.utc).isoformat(),
        channel_versions=checkpoint['channel_versions'],
        versions_seen=checkpoint['versions_seen'],
        channel_values=values
    )