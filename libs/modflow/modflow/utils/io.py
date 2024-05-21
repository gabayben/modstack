from typing import Any, Iterator, Mapping, Optional, Sequence, Union

from modflow.channels import Channel, EmptyChannelError

def read_channel(
    channels: Mapping[str, Channel],
    channel: str,
    catch: bool = True,
    return_exception: bool = False
) -> Any | BaseException:
    try:
        return channels[channel].get()
    except EmptyChannelError as e:
        if return_exception:
            return e
        elif catch:
            return None
        raise

def read_channels(
    channels: Mapping[str, Channel],
    select: Union[str, list[str]],
    skip_empty: bool = True
) -> Union[Any, dict[str, Any]]:
    if isinstance(select, str):
        return read_channel(channels, select)
    values: dict[str, Any] = {}
    for channel in select:
        try:
            values[channel] = read_channel(channels, channel, catch = not skip_empty)
        except EmptyChannelError:
            pass
    return values

def map_input(
    input_channels: Union[str, Sequence[str]],
    chunk: Optional[Union[Any, dict[str, Any]]]
) -> Iterator[tuple[str, Any]]:
    pass