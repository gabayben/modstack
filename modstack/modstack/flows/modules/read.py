from typing import Any, Callable, Optional, Union

from modstack.flows.constants import READ_KEY
from modstack.core import Modules

READ_TYPE = Callable[[Union[str, list[str]], bool], Union[Any, dict[str, Any]]]

class ChannelRead(Modules.Sync):
    def __init__(
        self,
        channels: Union[str, list[str]],
        fresh: bool = False,
        mapper: Optional[Callable[[Any], Any]] = None
    ):
        self.channels = channels
        self.fresh = fresh
        self.mapper = mapper

    def _invoke(self, _: Any, **kwargs) -> Any:
        return self.do_read(
            self.channels,
            fresh=self.fresh,
            mapper=self.mapper,
            **kwargs
        )

    def get_name(
        self,
        suffix: Optional[str] = None,
        name: Optional[str] = None
    ) -> str:
        if name:
            return name
        name = f'ChannelRead<{self.channels if isinstance(self.channels, str) else ', '.join(self.channels)}>'
        return super().get_name(name=name, suffix=suffix)

    @staticmethod
    def do_read(
        channels: Union[str, list[str]],
        fresh: bool = True,
        mapper: Optional[Callable[[Any], Any]] = None,
        **kwargs
    ) -> Any:
        try:
            read: READ_TYPE = kwargs.get(READ_KEY)
        except KeyError:
            raise RuntimeError(
                'Not configured with a read function. '
                'Make sure to call in the context of a Pregel process.'
            )
        if mapper:
            return mapper(read(channels, fresh))
        return read(channels, fresh)