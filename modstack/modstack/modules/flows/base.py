from abc import ABC
from typing import Type

import networkx
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from modstack.contracts.flows import SocketId
from modstack.endpoints import Endpoint
from modstack.engines import Engine
from modstack.modules import Module
from modstack.modules.flows import FlowConnectError, FlowError, FlowNode, NodeNotFound
from modstack.utils.func import tproduct
from modstack.utils.reflection import types_are_compatible

class FlowBase(Module, ABC):
    def __init__(self, engine: Engine):
        self.engine = engine
        self.graph = networkx.MultiDiGraph()

    def connect(
        self,
        source: SocketId,
        target: SocketId
    ) -> None:
        if source.node == target.node:
            raise FlowError(f'Source and target node are both {target.node}. Cannot connect node to itself.')
        source_schema = self._get_or_add_node(source.node).output_schema
        target_schema = self._get_or_add_node(target.node).input_schema
        source_field = self._get_field_info(source.node, source_schema, source.field)
        target_field = self._get_field_info(target.node, target_schema, target.field)

        source_candidates: list[tuple[str, FieldInfo]] = [
            source_field] if source_field else list(source_schema.model_fields.items())
        target_candidates: list[tuple[str, FieldInfo]] = [
            target_field] if target_field else list(target_schema.model_fields.items())

        possible_connections = (
            (source_cand, target_cand)
            for source_cand, target_cand in tproduct(source_candidates, target_candidates)
            if types_are_compatible(source_cand[1].annotation, target_cand[1].annotation)
        )

    def get_node(self, path: str) -> FlowNode:
        if not self.graph.has_node(path):
            raise NodeNotFound(f'Node with path {path} not found in graph.')
        return self.graph.nodes[path]

    def _get_or_add_node(self, path: str) -> Endpoint:
        if not self.graph.has_node(path):
            endpoint = self.engine.get_endpoint(path)
            self.graph.add_node(path, endpoint=endpoint, visits=0)
            return endpoint
        return self.graph.nodes[path]['endpoint']

    def _get_field_info(self, node: str, schema: Type[BaseModel], field: str | None) -> tuple[str, FieldInfo] | None:
        if field:
            info = schema.model_fields.get(field, None)
            if not info:
                raise FlowConnectError(f'Field {field} not found for node {node}.')
            return field, info
        elif len(schema.model_fields) == 1:
            return list(schema.model_fields.items())[0]
        return None