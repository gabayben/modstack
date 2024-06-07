from abc import ABC, abstractmethod
from typing import Optional

from modstack.stores.graph import GraphNode, GraphNodeQuery, GraphTriplet, GraphTripletQuery

class GraphStore(ABC):
    @abstractmethod
    def get(self, query: Optional[GraphNodeQuery] = None) -> list[GraphNode]:
        pass

    @abstractmethod
    async def aget(self, query: Optional[GraphNodeQuery] = None) -> list[GraphNode]:
        pass

    @abstractmethod
    def get_triplets(self, query: Optional[GraphTripletQuery] = None) -> list[GraphTriplet]:
        pass

    @abstractmethod
    async def aget_triplets(self, query: Optional[GraphTripletQuery] = None) -> list[GraphTriplet]:
        pass