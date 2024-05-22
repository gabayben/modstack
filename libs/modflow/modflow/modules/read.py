from typing import Any, Optional, Union

from modstack.modules import Functional

class ChannelRead(Functional):
    def __init__(
        self,
        channels: Union[str, list[str]],
        fresh: bool = False
    ):
        super().__init__(self._read)
        self.channels = channels
        self.fresh = fresh

    def get_name(
        self,
        suffix: Optional[str] = None,
        name: Optional[str] = None
    ) -> str:
        if name:
            return name
        name = f'ChannelRead<{self.channels if isinstance(self.channels, str) else ', '.join(self.channels)}>'
        return super().get_name(name=name, suffix=suffix)

    async def _read(self, _: Any) -> Any:
        #TODO: Read logic
        pass