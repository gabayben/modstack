import asyncio
from functools import partial
from typing import Any, Callable, NamedTuple, Optional, Sequence

from modflow.constants import IS_CHANNEL_WRITER, WRITE_KEY
from modstack.modules import Module, Passthrough, SerializableModule
from modstack.typing import Effect, Effects
from modstack.utils import tzip

SKIP_WRITE = object()
WRITE_TYPE = Callable[[Sequence[tuple[str, Any]]], None]
PASSTHROUGH = Passthrough()

class ChannelWriteEntry(NamedTuple):
    channel: str
    value: Any = PASSTHROUGH
    skip_none: bool = False
    mapper: Optional[Module] = None

class ChannelWrite(SerializableModule):
    def __init__(
        self,
        writes: Sequence[ChannelWriteEntry],
        tags: list[str] = [],
        **kwargs
    ):
        super().__init__(**kwargs)
        self.writes = writes
        self.tags = set(tags)

    def forward(self, data: Any, **kwargs) -> Effect[Any]:
        return Effects.Provide(
            invoke=partial(self._write, data, **kwargs),
            ainvoke=partial(self._awrite, data, **kwargs)
        )

    def _write(
        self,
        data: Any,
        **kwargs
    ) -> Any:
        values = [
            data if write.value is Passthrough else write.value
            for write in self.writes
        ]
        values = [
            write.mapper.invoke(value, **kwargs)
            if write.mapper
            else value
            for value, write in tzip(values, self.writes)
        ]
        values = [
            (write.channel, value)
            for value, write in tzip(values, self.writes)
            if not write.skip_none or value is not None
        ]
        self.do_write(data, kwargs)
        return data

    async def _awrite(
        self,
        data: Any,
        **kwargs
    ) -> Any:
        values = [
            data if write.value is Passthrough else write.value
            for write in self.writes
        ]
        values = await asyncio.gather(
            *(
                write.mapper.ainvoke(value, **kwargs)
                if write.mapper
                else _make_future(value)
                for value, write in tzip(values, self.writes)
            )
        )
        values = [
            (write.channel, value)
            for value, write in tzip(values, self.writes)
            if not write.skip_none or value is not None
        ]
        self.do_write(data, kwargs)
        return data

    @staticmethod
    def register_writer[M: Module](mod: M) -> M:
        object.__setattr__(mod, IS_CHANNEL_WRITER, True)
        return mod

    @staticmethod
    def is_writer(mod: Module) -> bool:
        return (
            isinstance(mod, ChannelWrite)
            or getattr(mod, IS_CHANNEL_WRITER, False) is True
        )

    @staticmethod
    def do_write(values: dict[str, Any], config: dict[str, Any]) -> None:
        write = config.get(WRITE_KEY)
        write([(chan, value) for chan, value in values.items() if value is not SKIP_WRITE])

def _make_future(value: Any) -> asyncio.Future:
    future = asyncio.Future()
    future.set_result(value)
    return future