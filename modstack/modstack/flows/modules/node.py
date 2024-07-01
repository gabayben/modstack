from typing import Any, Callable, Optional, Sequence, Union

from modstack.flows.modules import ChannelWrite
from modstack.core import DecoratorBase, Module, ModuleLike, Passthrough, Sequential, coerce_to_module
from modstack.core.base import ModuleMapping

DEFAULT_BOUND = Passthrough()

class PregelNode(DecoratorBase):
    channels: Union[list[str], dict[str, str]]
    triggers: list[str]
    writers: list[Module]
    mapper: Optional[Callable[[Any], Any]]

    def __init__(
        self,
        channels: Union[list[str], dict[str, str]],
        triggers: Sequence[str],
        writers: list[Module] = [],
        mapper: Optional[Callable[[Any], Any]] = None,
        bound: Module = DEFAULT_BOUND,
        tags: Optional[list[str]] = None,
        kwargs: dict[str, Any] = {}
    ):
        super().__init__(
            bound=bound,
            kwargs=kwargs,
            channels=channels,
            triggers=triggers,
            writers=writers,
            mapper=mapper,
            tags=tags or []
        )

    def __or__(self, other: Union[ModuleLike, ModuleMapping]) -> 'PregelNode':
        if ChannelWrite.is_writer(other):
            return PregelNode(
                bound=self.bound,
                channels=self.channels,
                triggers=self.triggers,
                writers=[*self.writers, other],
                mapper=self.mapper,
                kwargs=self.kwargs
            )
        elif self.bound is DEFAULT_BOUND:
            return PregelNode(
                bound=coerce_to_module(other),
                channels=self.channels,
                triggers=self.triggers,
                writers=self.writers,
                mapper=self.mapper,
                kwargs=self.kwargs
            )
        return PregelNode(
            bound=self.bound | other,
            channels=self.channels,
            triggers=self.triggers,
            writers=self.writers,
            mapper=self.mapper,
            kwargs=self.kwargs
        )

    def __ror__(self, other: ModuleLike) -> 'Module':
        raise NotImplementedError()

    def get_node(self) -> Optional[Module]:
        writers = self.get_writers()
        if self.bound is DEFAULT_BOUND and not writers:
            return None
        elif self.bound is DEFAULT_BOUND and len(writers) == 1:
            return writers[0]
        elif self.bound is DEFAULT_BOUND:
            return Sequential(*writers)
        elif writers:
            return Sequential(self.bound, *writers)
        return self.bound

    def get_writers(self) -> list[Module]:
        writers = self.writers.copy()
        while (
            len(writers) > 1
            and isinstance(writers[-1], ChannelWrite)
            and isinstance(writers[-2], ChannelWrite)
        ):
            writers[-2].writes += writers[-1].writes # type: ignore
            writers.pop()
        return writers