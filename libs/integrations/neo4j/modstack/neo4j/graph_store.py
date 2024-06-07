from typing import Any, Optional

from modstack.stores.graph import GraphNode, GraphNodeQuery, GraphRelation, GraphStore, GraphTriplet, GraphTripletQuery
from modstack.stores.vector import VectorStoreQuery
from modstack.typing import Embedding

class Neo4jGraphStore(GraphStore):
    def structured_query(
        self, query: str,
        param_map: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        pass

    async def astructured_query(
        self,
        query: str,
        param_map: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        pass

    def vector_query(self, query: VectorStoreQuery, **kwargs) -> tuple[list[GraphNode], Embedding]:
        pass

    async def avector_query(self, query: VectorStoreQuery, **kwargs) -> tuple[list[GraphNode], Embedding]:
        pass

    def get(self, query: Optional[GraphNodeQuery] = None) -> list[GraphNode]:
        pass

    async def aget(self, query: Optional[GraphNodeQuery] = None) -> list[GraphNode]:
        pass

    def get_triplets(self, query: Optional[GraphTripletQuery] = None) -> list[GraphTriplet]:
        pass

    async def aget_triplets(self, query: Optional[GraphTripletQuery] = None) -> list[GraphTriplet]:
        pass

    def get_rel_map(
        self,
        nodes: list[GraphNode],
        ignore_rels: Optional[list[str]] = None,
        depth: int = 2,
        limit: int = 30,
        **kwargs
    ) -> list[GraphTriplet]:
        pass

    async def aget_rel_map(
        self,
        nodes: list[GraphNode],
        ignore_rels: Optional[list[str]] = None,
        depth: int = 2,
        limit: int = 30,
        **kwargs
    ) -> list[GraphTriplet]:
        pass

    def upsert_nodes(self, nodes: list[GraphNode], **kwargs) -> None:
        pass

    async def aupsert_nodes(self, nodes: list[GraphNode], **kwargs) -> None:
        pass

    def upsert_relations(self, relations: list[GraphRelation], **kwargs) -> None:
        pass

    async def aupsert_relations(self, relations: list[GraphRelation], **kwargs) -> None:
        pass

    def delete(self, query: Optional[GraphNodeQuery] = None) -> None:
        pass

    async def adelete(self, query: Optional[GraphNodeQuery] = None) -> None:
        pass