from abc import ABC, abstractmethod
from typing import Any, Optional

import fsspec

from modstack.artifacts import Artifact, ArtifactRelationship
from modstack.data.stores import ChunkNode, GraphNode, GraphNodeQuery, GraphRelation, GraphTriplet, GraphTripletQuery, VectorStoreQuery
from modstack.typing import Embedding
from modstack.utils.constants import GRAPH_TRIPLET_SOURCE_KEY

class GraphStore(ABC):
    @property
    def supports_structured_query(self) -> bool:
        return False

    @property
    def supports_vector_query(self) -> bool:
        return False

    @abstractmethod
    def persist(
        self,
        path: str,
        fs: Optional[fsspec.AbstractFileSystem] = None,
        **kwargs
    ) -> None:
        pass

    @abstractmethod
    def structured_query(
        self,
        query: str,
        param_map: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        pass

    @abstractmethod
    async def astructured_query(
        self,
        query: str,
        param_map: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        pass

    @abstractmethod
    def vector_query(self, query: VectorStoreQuery, **kwargs) -> tuple[list[GraphNode], Embedding]:
        pass

    @abstractmethod
    async def avector_query(self, query: VectorStoreQuery, **kwargs) -> tuple[list[GraphNode], Embedding]:
        pass

    @abstractmethod
    def get(self, query: Optional[GraphNodeQuery] = None) -> list[GraphNode]:
        pass

    @abstractmethod
    async def aget(self, query: Optional[GraphNodeQuery] = None) -> list[GraphNode]:
        pass

    def get_artifacts(self, node_ids: list[str]) -> list[Artifact]:
        nodes = self.get(GraphNodeQuery(ids=node_ids))
        return [node.to_artifact() for node in nodes]

    async def aget_artifacts(self, node_ids: list[str]) -> list[Artifact]:
        nodes = await self.aget(GraphNodeQuery(ids=node_ids))
        return [node.to_artifact() for node in nodes]

    @abstractmethod
    def get_triplets(self, query: Optional[GraphTripletQuery] = None) -> list[GraphTriplet]:
        pass

    @abstractmethod
    async def aget_triplets(self, query: Optional[GraphTripletQuery] = None) -> list[GraphTriplet]:
        pass

    @abstractmethod
    def get_rel_map(
        self,
        nodes: list[GraphNode],
        ignore_rels: Optional[list[str]] = None,
        depth: int = 2,
        limit: int = 30,
        **kwargs
    ) -> list[GraphTriplet]:
        pass

    @abstractmethod
    async def aget_rel_map(
        self,
        nodes: list[GraphNode],
        ignore_rels: Optional[list[str]] = None,
        depth: int = 2,
        limit: int = 30,
        **kwargs
    ) -> list[GraphTriplet]:
        pass

    @abstractmethod
    def upsert_nodes(self, nodes: list[GraphNode], **kwargs) -> None:
        pass

    @abstractmethod
    async def aupsert_nodes(self, nodes: list[GraphNode], **kwargs) -> None:
        pass

    def upsert_artifacts(self, artifacts: list[Artifact], **kwargs) -> None:
        self.upsert_nodes(
            [ChunkNode.from_artifact(artifact) for artifact in artifacts],
            **kwargs
        )

    async def aupsert_artifacts(self, artifacts: list[Artifact], **kwargs) -> None:
        await self.aupsert_nodes(
            [ChunkNode.from_artifact(artifact) for artifact in artifacts],
            **kwargs
        )

    @abstractmethod
    def upsert_relations(self, relations: list[GraphRelation], **kwargs) -> None:
        pass

    @abstractmethod
    async def aupsert_relations(self, relations: list[GraphRelation], **kwargs) -> None:
        pass

    @abstractmethod
    def delete(self, query: Optional[GraphNodeQuery] = None) -> None:
        pass

    @abstractmethod
    async def adelete(self, query: Optional[GraphNodeQuery] = None) -> None:
        pass

    def delete_artifacts(
        self,
        artifact_ids: Optional[list[str]] = None,
        ref_artifact_ids: Optional[list[str]] = None
    ) -> None:
        nodes: list[GraphNode] = []

        artifact_ids = artifact_ids or []
        for artifact_id in artifact_ids:
            nodes.extend(self.get(
                GraphNodeQuery(properties={GRAPH_TRIPLET_SOURCE_KEY: artifact_id})
            ))

        if len(artifact_ids) > 0:
            nodes.extend(self.get(
                GraphNodeQuery(ids=artifact_ids)
            ))

        ref_artifact_ids = ref_artifact_ids or []
        for ref_artifact_id in artifact_ids:
            nodes.extend(self.get(
                GraphNodeQuery(properties={
                    'relationships': {ArtifactRelationship.REF: ref_artifact_id}
                })
            ))

        if len(ref_artifact_ids) > 0:
            nodes.extend(self.get(
                GraphNodeQuery(ids=ref_artifact_ids)
            ))

        if len(nodes) > 0:
            self.delete(
                GraphNodeQuery(ids=[node.id for node in nodes])
            )

    async def adelete_artifacts(
        self,
        artifact_ids: Optional[list[str]] = None,
        ref_artifact_ids: Optional[list[str]] = None
    ) -> None:
        nodes: list[GraphNode] = []

        artifact_ids = artifact_ids or []
        for artifact_id in artifact_ids:
            nodes.extend(await self.aget(
                GraphNodeQuery(properties={GRAPH_TRIPLET_SOURCE_KEY: artifact_id})
            ))

        if len(artifact_ids) > 0:
            nodes.extend(await self.aget(
                GraphNodeQuery(ids=artifact_ids)
            ))

        ref_artifact_ids = ref_artifact_ids or []
        for ref_artifact_id in artifact_ids:
            nodes.extend(await self.aget(
                GraphNodeQuery(properties={
                    'relationships': {ArtifactRelationship.REF: ref_artifact_id}
                })
            ))

        if len(ref_artifact_ids) > 0:
            nodes.extend(await self.aget(
                GraphNodeQuery(ids=ref_artifact_ids)
            ))

        if len(nodes) > 0:
            await self.adelete(
                GraphNodeQuery(ids=[node.id for node in nodes])
            )