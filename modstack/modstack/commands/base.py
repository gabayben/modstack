from abc import ABC, abstractmethod
import inspect
from typing import Any, AsyncIterator, Callable, Generic, Iterator, Type, TypeVar

from pydantic import BaseModel

from modstack.constants import IGNORE_OUTPUT_SCHEMA, MODSTACK_COMMAND
from modstack.containers import Effect, Effects
from modstack.typing import Serializable
from modstack.typing.vars import Out
from modstack.utils.serialization import create_model, create_schema

class Command(Serializable, Generic[Out], ABC):
    @classmethod
    @abstractmethod
    def name(cls) -> str:
        return cls.__name__

TCommand = TypeVar('TCommand', bound=Command)

class CommandHandler(Generic[TCommand, Out]):
    _call: Callable[..., Effect[Out]]
    contract: Type[TCommand]
    return_annotation: Any
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]

    def __init__(self, func: Callable[..., Out]):
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

        self._call = fn
        signature = inspect.signature(func)
        self.command = getattr(self, MODSTACK_COMMAND)
        self.return_annotation = signature.return_annotation
        self.input_schema = self.command
        self.output_schema = (
            create_schema(
                f'{self.command.name()}_Output',
                self.return_annotation
            )
            if not getattr(self, IGNORE_OUTPUT_SCHEMA, False)
            else create_model(f'{self.command.name()}_Output', value=(self.return_annotation, None))
        )

    def __call__(self, *args, **kwargs) -> Effect[Out]:
        return self._call(*args, **kwargs)

    def effect(self, command: TCommand) -> Effect[Out]:
        return self(command)

    def invoke(self, command: TCommand) -> Out:
        return self.effect(command).invoke()

    async def ainvoke(self, command: TCommand) -> Out:
        return await self.effect(command).ainvoke()

    def iter(self, command: TCommand) -> Iterator[Out]:
        yield from self.effect(command).iter()

    async def aiter(self, command: TCommand) -> AsyncIterator[Out]:
        async for item in self.effect(command).aiter(): #type: ignore
            yield item

class CommandNotFound(Exception):
    pass

class AmbiguousCommands(Exception):
    pass

def command(
    command: Type[TCommand],
    ignore_output_schema: bool = False
) -> Callable[..., Out]:
    def wrapper(fn: Callable[..., Out]) -> Callable[..., Out]:
        setattr(fn, MODSTACK_COMMAND, command)
        setattr(fn, IGNORE_OUTPUT_SCHEMA, ignore_output_schema)
        return fn
    return wrapper

def command_handler(
    command: Type[TCommand],
    ignore_output_schema: bool = False
) -> CommandHandler[[TCommand], Out]:
    def wrapper(fn: Callable[..., Out]) -> CommandHandler[[TCommand], Out]:
        setattr(fn, MODSTACK_COMMAND, True)
        return CommandHandler(fn)
    return wrapper #type: ignore