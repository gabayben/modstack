"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/graphs/state.py
"""

import inspect
import logging
from typing import Optional, Type, Union, get_origin, get_type_hints, override

from pydantic import BaseModel

from modflow.channels import BinaryOperatorAggregate, Channel, LastValue
from modflow.managed import ManagedValue, is_managed_value
from modflow.modules import CompiledFlow, Flow
from modstack.modules import ModuleLike
from modstack.utils.serialization import create_schema

logger = logging.getLogger(__name__)

class StateFlow(Flow):
    channels: dict[str, Channel]
    managed_values: dict[str, Type[ManagedValue]]

    @override
    @property
    def _all_edges(self) -> set[tuple[str, str]]:
        return self.edges | {
            (source, end)
            for sources, end in self.waiting_edges
            for source in sources
        }

    def __init__(self, schema: Type):
        super().__init__()
        self.schema = schema
        self.channels, self.managed_values = _get_channels(schema)
        if any(isinstance(c, BinaryOperatorAggregate) for c in self.channels.values()):
            self._supports_multiple_edges = True
        self.waiting_edges: set[tuple[tuple[str, ...], str]] = set()

    @override
    def add_node(
        self,
        node: ModuleLike,
        name: Optional[str] = None
    ) -> None:
        pass

    @override
    def add_edge(
        self,
        source: Union[str, list[str]],
        target: str
    ) -> None:
        pass

class CompiledStateFlow(CompiledFlow):
    builder: StateFlow

    @override
    @property
    def input_schema(self) -> Type[BaseModel]:
        return create_schema(
            self.get_name(suffix='Input'),
            self.builder.schema #type: ignore
        )

    @override
    @property
    def output_schema(self) -> Type[BaseModel]:
        return create_schema(
            self.get_name(suffix='Output'),
            self.builder.schema #type: ignore
        )

def _get_channels(schema: Type) -> tuple[dict[str, Channel], dict[str, Type[ManagedValue]]]:
    if not hasattr(schema, '__annotations__'):
        return {'__root__': _get_channel(schema, allow_managed=False)}, {}

    all_values = {
        name: _get_channel(type_)
        for name, type_ in get_type_hints(schema, include_extras=True).items()
        if name != '__slots__'
    }

    # noinspection PyTypeChecker
    return (
        {k: v for k, v in all_values.items() if not is_managed_value(v)},
        {k: v for k, v in all_values.items() if is_managed_value(v)}
    )

def _get_channel(type_: Type, allow_managed: bool = True) -> Union[Channel, Type[ManagedValue]]:
    if managed_value := _is_field_managed_value(type_):
        if allow_managed:
            return managed_value
        raise ValueError(f'{type_} not allowed in this position.')

    if channel := _is_field_binary_op(type_):
        return channel

    return LastValue(type_) #type: ignore[call-args]

def _is_field_binary_op(type_: Type) -> Optional[BinaryOperatorAggregate]:
    if hasattr(type_, '__metadata__'):
        metadata = type_.__metadata__
        if len(metadata) == 1 and callable(metadata[0]):
            signature = inspect.signature(metadata[0])
            params = list(signature.parameters.values())
            if (
                len(params) == 2
                and len([
                    p
                    for p in params
                    if p in [p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD]
                ])
            ):
                return BinaryOperatorAggregate(type_, metadata[0]) #type: ignore[call-args]
    return None

def _is_field_managed_value(type_: Type) -> Optional[Type[ManagedValue]]:
    if hasattr(type_, '__metadata__'):
        metadata = type_.__metadata__
        if len(metadata) == 1:
            decoration = get_origin(metadata[0]) or metadata[0]
            if is_managed_value(decoration):
                return decoration #type: ignore
    return None