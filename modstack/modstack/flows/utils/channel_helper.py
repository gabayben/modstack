from typing import Optional, Sequence, Union, cast

from modstack.flows.modules import PregelNode

class ChannelHelper:
    @classmethod
    def subscribe_to(
        cls,
        channels: Union[str, Sequence[str]],
        key: Optional[str] = None,
        tags: Optional[list[str]] = None
    ) -> PregelNode:
        if not isinstance(channels, str) and key is not None:
            raise ValueError("Can't specify a key when subscribing to multiple channels.")
        return PregelNode(
            channels=cast(
                Union[dict[None, str], dict[str, str]],
                {key: channels}
                if isinstance(channels, str) and key is not None
                else [channels]
                if isinstance(channels, str)
                else {chan: chan for chan in channels}
            ),
            triggers=[channels] if isinstance(channels, str) else channels,
            tags=tags
        )