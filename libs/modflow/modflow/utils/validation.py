from typing import Mapping, Optional, Sequence, Type, Union

from modflow.channels import Channel
from modflow.flows import PregelNode

def validate_pipeline(
    nodes: Mapping[str, PregelNode],
    channels: Mapping[str, Channel],
    default_channel_type: Type[Channel],
    input_channels: Union[str, Sequence[str]],
    output_channels: Union[str, Sequence[str]],
    stream_channels: Optional[Union[str, Sequence[str]]],
    interrupt_before_nodes: Sequence[str],
    interrupt_after_nodes: Sequence[str]
) -> None:
    pass