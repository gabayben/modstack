"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/managed/few_shot.py
"""

from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, AsyncIterator, Callable, Generator, Iterator, Optional, Self, Sequence, TYPE_CHECKING, Union

from modstack.flows import PregelTaskDescription
from modstack.flows.channels import AsyncChannelManager, ChannelManager
from modstack.flows.managed import ManagedValue
from modstack.flows.managed.base import V
from modstack.flows.utils.io import read_channels

if TYPE_CHECKING:
    pass

_MetadataFilter = Union[dict[str, Any], Callable[..., dict[str, Any]]]

class FewShotExamples(ManagedValue[Sequence[V]]):
    examples: list[V]

    @property
    def metadata_filter_dict(self) -> dict[str, Any]:
        if isinstance(self.metadata_filter, Callable):
            return self.metadata_filter(**self.kwargs)
        return self.metadata_filter

    def __init__(
        self,
        flow: 'Pregel',
        k: int = 5,
        metadata_filter: Optional[_MetadataFilter] = None,
        **kwargs
    ):
        super().__init__(flow, **kwargs)
        self.k = k
        self.metadata_filter = metadata_filter or {}

    @classmethod
    @contextmanager
    def enter(cls, flow: 'Pregel', **kwargs) -> Generator[Self, None, None]:
        with super().enter(flow, **kwargs) as value:
            value.examples = list(value.iter())
            yield value

    @classmethod
    @asynccontextmanager
    def aenter(cls, flow: 'Pregel', **kwargs) -> AsyncGenerator[Self, None]:
        async with super().aenter(flow, **kwargs) as value:
            value.examples = [e async for e in value.aiter()]
            yield value

    def iter(self, score: int = 1) -> Iterator[V]:
        for example in self.flow.checkpointer.get_many({
            'score': score,
            **self.metadata_filter_dict
        }, limit=self.k):
            with ChannelManager(self.flow.channels, example.checkpoint) as channels:
                yield read_channels(channels, self.flow.output_channels)

    async def aiter(self, score: int = 1) -> AsyncIterator[V]:
        # noinspection PyTypeChecker
        async for example in self.flow.checkpointer.aget_many({
            'score': score,
            **self.metadata_filter_dict
        }, limit=self.k):
            async with AsyncChannelManager(self.flow.channels, example.checkpoint) as channels:
                yield read_channels(channels, self.flow.output_channels)

    def __call__(self, step: int, task: PregelTaskDescription) -> Sequence[V]:
        return self.examples