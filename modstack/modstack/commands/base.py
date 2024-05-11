from abc import ABC
import inspect
from typing import AsyncIterator, Callable, Generic, Iterator, Type, TypeVar, final

from pydantic import BaseModel

from modstack.constants import COMMAND_TYPE, IGNORE_OUTPUT_SCHEMA
from modstack.containers import Effect, Effects, ReturnType
from modstack.typing import Serializable
from modstack.typing.vars import Out
from modstack.utils.serialization import create_model, create_schema

class Command(Serializable, Generic[Out], ABC):
    pass

TCommand = TypeVar('TCommand', bound=Command)

@final
class CommandHandler(Generic[TCommand, Out]):
    _func: Callable[..., Effect[Out]]
    command_type: Type[TCommand]
    input_schema: Type[BaseModel]
    output_type: Type[Out]
    output_schema: Type[BaseModel]

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
        self.input_schema = self.command_type
        self.output_type = inspect.signature(func).return_annotation
        self.output_schema = (
            create_schema(f'{self.command_type.__name__}Output', type(Out))
            if not getattr(func, IGNORE_OUTPUT_SCHEMA, False)
            else create_model(f'{self.command_type.__name__}Output', value=(self.output_type, None))
        )

    def effect(self, command: TCommand) -> Effect[Out]:
        return self._func(**dict(command))

    def invoke(self, command: TCommand) -> Out:
        return self.effect(command).invoke()

    async def ainvoke(self, command: TCommand) -> Out:
        return await self.effect(command).ainvoke()

    def iter(self, command: TCommand) -> Iterator[Out]:
        yield from self.effect(command).iter()

    async def aiter(self, command: TCommand) -> AsyncIterator[Out]:
        async for item in self.effect(command).aiter(): #type: ignore
            yield item

def command(
    command_type: Type[TCommand],
    ignore_output_schema: bool = False
):
    def wrapper(func: Callable[..., ReturnType[Out]]) -> Callable[..., ReturnType[Out]]:
        setattr(func, COMMAND_TYPE, command_type)
        setattr(func, IGNORE_OUTPUT_SCHEMA, ignore_output_schema)
        return func
    return wrapper

def command_handler(command_type: Type[TCommand]):
    def wrapper(func: Callable[..., ReturnType[Out]]) -> CommandHandler[TCommand, Out]:
        setattr(func, COMMAND_TYPE, command_type)
        return CommandHandler(func)
    return wrapper