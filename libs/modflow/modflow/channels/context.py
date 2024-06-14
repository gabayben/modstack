"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/context.py
"""

from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncContextManager, AsyncGenerator, Callable, Generator, Optional, Self, Sequence, Type

from decorator import ContextManager

from modflow.channels import Channel, EmptyChannelError, InvalidUpdateError

class ContextValue[Value](Channel[Value, None, None]):
    """
    Taken from LangGraph's Context.
    Exposes the value of a context manager, for the duration of an invocation.
    Context manager is entered before the first step, and exited after the last step.
    Optionally, provide an equivalent async context manager, which will be used
    instead for async invocations.
    """

    value: Value

    @property
    def ValueType(self) -> Optional[Any]:
        return (
            self.type_
            or (self.ctx if hasattr(self.ctx, '__enter__') else None)
            or (self.actx if hasattr(self.actx, '__aenter__') else None)
            or None
        )

    @property
    def UpdateType(self) -> Optional[Any]:
        return None

    def __init__(
        self,
        type_: Optional[Type[Value]] = None,
        ctx: Optional[Callable[[], ContextManager[Value]]] = None,
        actx: Optional[Callable[[], AsyncContextManager[Value]]] = None
    ):
        if ctx is None and actx is None:
            raise ValueError('Must provide either sync or async context manager.')
        self.type_ = type_
        self.ctx = ctx
        self.actx = actx

    @contextmanager
    def new(self, checkpoint: Optional[None] = None) -> Generator[Self, None, None]:
        if self.ctx is None:
            raise ValueError('Cannot enter sync context manager.')
        empty = self.__class__(type_=self.type_, ctx=self.ctx, actx=self.actx)
        ctx = self.ctx()
        empty.value = ctx.__enter__()
        try:
            yield empty
        finally:
            ctx.__exit__(None, None, None)

    @asynccontextmanager
    async def anew(self, checkpoint: Optional[None] = None) -> AsyncGenerator[Self, None, None]:
        if self.actx is not None:
            empty = self.__class__(type_=self.type_, ctx=self.ctx, actx=self.actx)
            actx = self.actx()
            empty.value = await actx.__aenter__()
            try:
                yield empty
            finally:
                await actx.__aexit__(None, None, None)
        else:
            with self.new(checkpoint) as empty:
                yield empty

    def checkpoint(self) -> Optional[None]:
        raise EmptyChannelError()

    def get(self) -> Optional[Value]:
        try:
            return self.value
        except AttributeError:
            raise EmptyChannelError()

    def update(self, values: Optional[Sequence[None]]) -> None:
        if values:
            raise InvalidUpdateError()