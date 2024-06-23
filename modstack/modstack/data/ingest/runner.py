from functools import partial
from typing import AsyncIterator, Iterable, Iterator, final

from modstack.artifacts import Artifact
from modstack.data import IngestConnector
from modstack.modules import SerializableModule
from modstack.typing import Effect, Effects

class IngestRunner(SerializableModule[IngestConnector, Iterable[Artifact]]):
    @final
    def forward(self, data: IngestConnector, **kwargs) -> Effect[Iterable[Artifact]]:
        return Effects.From(
            invoke=partial(self._invoke, data, **kwargs),
            ainvoke=partial(self._ainvoke, data, **kwargs),
            iter_=partial(self._stream, data, **kwargs),
            aiter_=partial(self._astream, data, **kwargs)
        )

    def _invoke(self, data: IngestConnector, **kwargs) -> Iterable[Artifact]:
        pass

    async def _ainvoke(self, data: IngestConnector, **kwargs) -> Iterable[Artifact]:
        pass

    def _stream(self, data: IngestConnector, **kwargs) -> Iterator[Iterable[Artifact]]:
        pass

    async def _astream(self, data: IngestConnector, **kwargs) -> AsyncIterator[Iterable[Artifact]]:
        pass