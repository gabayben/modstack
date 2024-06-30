from functools import partial
from typing import AsyncIterator, Iterator, final

from modstack.artifacts.layout import Element
from modstack.data.ingest import IngestDocument
from modstack.modules import SerializableModule
from modstack.typing import Effect, Effects

class IngestRunner(SerializableModule[list[IngestDocument], list[Element]]):
    @final
    def forward(self, data: list[IngestDocument], **kwargs) -> Effect[list[Element]]:
        return Effects.From(
            invoke=partial(self._invoke, data, **kwargs),
            ainvoke=partial(self._ainvoke, data, **kwargs),
            iter_=partial(self._stream, data, **kwargs),
            aiter_=partial(self._astream, data, **kwargs)
        )

    def _invoke(self, data: list[IngestDocument], **kwargs) -> list[Element]:
        pass

    async def _ainvoke(self, data: list[IngestDocument], **kwargs) -> list[Element]:
        pass

    def _stream(self, data: list[IngestDocument], **kwargs) -> Iterator[list[Element]]:
        pass

    async def _astream(self, data: list[IngestDocument], **kwargs) -> AsyncIterator[list[Element]]:
        pass