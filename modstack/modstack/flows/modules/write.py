import asyncio
from functools import partial
from typing import Any, Callable, NamedTuple, Optional, Sequence

from modstack.flows import Send
from modstack.flows.channels import InvalidUpdateError
from modstack.flows.constants import IS_CHANNEL_WRITER, TASKS, WRITE_KEY
from modstack.modules import Module, Passthrough, SerializableModule
from modstack.typing import Effect, Effects
from modstack.utils.func import tzip

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
        require_at_least_one_of: Optional[Sequence[str]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.writes = writes
        self.tags = set(tags)
        self.require_at_least_one_of = require_at_least_one_of

    def forward(self, data: Any, **kwargs) -> Effect[Any]:
        return Effects.From(
            invoke=partial(self._write, data, **kwargs),
            ainvoke=partial(self._awrite, data, **kwargs)
        )

    def _write(
        self,
        data: Any,
        **kwargs
    ) -> Any:
        # split packets and entries
        writes = [(TASKS, write) for write in self.writes if isinstance(write, Send)]
        entries = [write for write in self.writes if isinstance(write, ChannelWriteEntry)]
        for entry in entries:
            if entry.channel == TASKS:
                raise InvalidUpdateError(f'Cannot write to the reserved channel {TASKS}.')

        # process entries into values
        values = [
            data if write.value is Passthrough else write.value
            for write in entries
        ]
        values = [
            write.mapper.invoke(value, **kwargs)
            if write.mapper
            else value
            for value, write in tzip(values, entries)
        ]
        values = [
            (write.channel, value)
            for value, write in tzip(values, entries)
            if not write.skip_none or value is not None
        ]

        # write packets and values
        self.do_write(
            writes + values,
            kwargs,
            require_at_least_one_of=self.require_at_least_one_of if data is not None else None
        )

        return data

    async def _awrite(
        self,
        data: Any,
        **kwargs
    ) -> Any:
        # split packets and entries
        writes = [(TASKS, write) for write in self.writes if isinstance(write, Send)]
        entries = [write for write in self.writes if isinstance(write, ChannelWriteEntry)]
        for entry in entries:
            if entry.channel == TASKS:
                raise InvalidUpdateError(f'Cannot write to the reserved channel {TASKS}.')

        # process entries into values
        values = [
            data if write.value is Passthrough else write.value
            for write in entries
        ]
        values = await asyncio.gather(
            *(
                write.mapper.ainvoke(value, **kwargs)
                if write.mapper
                else _make_future(value)
                for value, write in tzip(values, entries)
            )
        )
        values = [
            (write.channel, value)
            for value, write in tzip(values, entries)
            if not write.skip_none or value is not None
        ]

        # write packets and values
        self.do_write(
            writes + values,
            kwargs,
            require_at_least_one_of=self.require_at_least_one_of if data is not None else None
        )

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
    def do_write(
        values: list[tuple[str, Any]],
        config: dict[str, Any],
        require_at_least_one_of: Optional[Sequence[str]] = None
    ) -> None:
        filtered = [(chan, value) for chan, value in values if value is not SKIP_WRITE]
        if require_at_least_one_of is not None:
            if not {chan for chan, _ in filtered} and set(require_at_least_one_of):
                raise InvalidUpdateError(f'Must write to at least one of {require_at_least_one_of}.')
        write: WRITE_TYPE = config.get(WRITE_KEY)
        write(filtered)

def _make_future(value: Any) -> asyncio.Future:
    future = asyncio.Future()
    future.set_result(value)
    return future