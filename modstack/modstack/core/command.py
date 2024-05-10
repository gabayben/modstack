from abc import ABC
import inspect
from typing import AsyncIterator, Callable, Generic, Iterator, Protocol, Type, TypeVar, final

from modstack.constants import COMMAND_TYPE
from modstack.containers import Effect, Effects, ReturnType
from modstack.core import Serializable
from modstack.typing.vars import Out

class Command(Serializable, Generic[Out], ABC):
    pass

TCommand = TypeVar('TCommand', bound=Command)

@final
class CommandHandler(Generic[TCommand, Out]):
    _func: Callable[..., Effect[Out]]
    command_type: Type[TCommand]
    output_type: Type[Out]

    def __init__(self, func: Callable[..., ReturnType[Out]]):
        def fn(*args, **kwargs) -> Effect[Out]:
            if inspect.isasyncgenfunction(func):
                async def _fn() -> AsyncIterator[Out]:
                    async for item in func(*args, **kwargs):
                        yield item
                return Effects.AsyncIterator(_fn)
            elif inspect.isabstract(func):
                def _fn() -> Iterator[Out]:
                    yield from func(*args, **kwargs)
                return Effects.Iterator(_fn)
            elif inspect.iscoroutinefunction(func):
                async def _fn() -> Out:
                    return await func(*args, **kwargs)
                return Effects.Async(_fn)
            else:
                def _fn() -> Out:
                    return func(*args, **kwargs)
                return Effects.Sync(_fn)

        self._func = fn
        self.command_type = getattr(func, COMMAND_TYPE)
        self.output_type = inspect.signature(func).return_annotation

    def effect(self, command: TCommand) -> Effect[Out]:
        return self._func(**command.model_dump())

    def invoke(self, command: TCommand) -> Out:
        return self.effect(command).invoke()

    async def ainvoke(self, command: TCommand) -> Out:
        return await self.effect(command).ainvoke()

    def iter(self, command: TCommand) -> Iterator[Out]:
        yield from self.effect(command).iter()

    async def aiter(self, command: TCommand) -> AsyncIterator[Out]:
        async for item in self.effect(command).aiter(): #type: ignore
            yield item

class CommandExecutor(Protocol[Out]):
    def evaluate(self, command: Command[Out]) -> Effect[Out]:
        pass

def command(command_type: Type[TCommand]):
    def wrapper(func: Callable[..., ReturnType[Out]]) -> Callable[..., ReturnType[Out]]:
        setattr(func, COMMAND_TYPE, command_type)
        return func
    return wrapper

def command_handler(command_type: Type[TCommand]):
    def wrapper(func: Callable[..., ReturnType[Out]]) -> CommandHandler[TCommand, Out]:
        setattr(func, COMMAND_TYPE, command_type)
        return CommandHandler(func)
    return wrapper