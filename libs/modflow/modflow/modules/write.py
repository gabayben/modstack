import asyncio
from typing import Any, NamedTuple, Optional, Sequence, Union

from modstack.modules import Functional, Module
from modstack.utils.func import tzip

class ChannelWriteEntry(NamedTuple):
    channel: str
    value: Optional[Union[Module, Any]] = None
    skip_none: bool = False

class ChannelWrite(Functional):
    def __init__(self, writes: Sequence[ChannelWriteEntry]):
        super().__init__(self._write)
        self.writes = writes

    async def _write(self, data: Any, **kwargs) -> Any:
        values = await asyncio.gather(
            *(
                write.value.ainvoke(data, **kwargs)
                if isinstance(write.value, Module)
                else _make_future(write.value)
                if write.value is not None
                else _make_future(data)
                for write in self.writes
            )
        )
        values = [
            (channel, value)
            for value, (channel, _, skip_none) in tzip(values, self.writes)
            if not skip_none or value is not None
        ]
        # TODO: Write logic
        return data

    @staticmethod
    def is_writer(mod: Module) -> bool:
        return (
            isinstance(mod, ChannelWrite)
            or getattr(mod, '_is_channel_writer', False) is True
        )

def _make_future(value: Any) -> asyncio.Future:
    future = asyncio.Future()
    future.set_result(value)
    return future