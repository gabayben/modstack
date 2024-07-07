from dataclasses import dataclass, field
from typing import Optional, Sequence, Unpack, override

from modstack.ai import Embedder, LLM
from modstack.ai.utils import aembed_artifacts, embed_artifacts
from modstack.artifacts import Artifact
from modstack.config import Settings
from modstack.core import ArtifactTransform, ArtifactTransformLike, Module, coerce_to_module
from modstack.core.utils import arun_transformations, run_transformations
from modstack.query.helpers import ImplicitGraphExtractor, SimpleLLMGraphExtractor
from modstack.query.indices import IndexData, Indexer
from modstack.query.indices.base import IndexDependencies
from modstack.query.indices.common import CommonIndex
from modstack.query.structs import GraphStruct
from modstack.stores import GraphNode, GraphRelation, GraphStore, VectorStore
from modstack.utils.constants import GRAPH_NODES_KEY, GRAPH_RELATIONS_KEY, GRAPH_TRIPLET_SOURCE_KEY

class GraphIndexDependencies(IndexDependencies, total=False):
    graph_store: GraphStore
    vector_store: VectorStore
    embedder: Embedder
    llm: LLM
    graph_extractors: Optional[list[ArtifactTransformLike]]
    embed_nodes: bool

@dataclass(kw_only=True)
class GraphIndex(CommonIndex[GraphStruct]):
    graph_store: GraphStore = field(default=Settings.graph_store)
    vector_store: Optional[VectorStore] = field(default=None)
    embedder: Embedder = field(default=Settings.embedder)
    llm: LLM = field(default=Settings.llm)
    graph_extractors: Optional[list[ArtifactTransformLike]] = field(default=None)
    embed_nodes: bool = field(default=True)

    def __post_init__(self):
        super().__post_init__()
        self.graph_extractors: list[ArtifactTransform] = (
            [coerce_to_module(extractor) for extractor in self.graph_extractors]
            if self.graph_extractors
            else [
                SimpleLLMGraphExtractor(llm=self.llm),
                ImplicitGraphExtractor()
            ]
        )

    @classmethod
    def indexer(cls, **kwargs: Unpack[GraphIndexDependencies]) -> Module[IndexData[GraphStruct], 'GraphIndex']:
        return Indexer(cls(**kwargs))

    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> GraphStruct:
        chunks = self._insert_chunks(list(artifacts), **kwargs)
        struct = GraphStruct()
        struct.artifact_ids = {chunk.id for chunk in chunks}
        return struct

    @override
    async def _abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> GraphStruct:
        chunks = await self._ainsert_chunks(list(artifacts), **kwargs)
        struct = GraphStruct()
        struct.artifact_ids = {chunk.id for chunk in chunks}
        return struct

    def _insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        chunks = self._insert_chunks(artifacts, **kwargs)
        for chunk in chunks:
            self.struct.add_artifact(chunk.id)

    def _insert_chunks(self, chunks: list[Artifact], **kwargs) -> list[Artifact]:
        if len(chunks) == 0:
            return chunks

        # run transformations on chunks and extract triplets
        chunks = run_transformations(
            chunks,
            self.graph_extractors,
            cache=self.cache,
            cache_collection=self.cache_collection
        )
        nodes_to_insert, relations_to_insert = self._extract_triplets(chunks)

        # filter out duplicate nodes
        existing_nodes = self.graph_store.get(ids=list({node.id for node in nodes_to_insert}))
        existing_node_ids = list({node.id for node in existing_nodes})
        del existing_nodes
        nodes_to_insert = [node for node in nodes_to_insert if node.id not in existing_node_ids]

        # filter out duplicate chunks
        existing_chunks = self.graph_store.get_artifacts([chunk.id for chunk in chunks])
        existing_chunk_hashes = {chunk.get_hash() for chunk in chunks}
        del existing_chunks
        chunk = [chunk for chunk in chunks if chunk.get_hash() not in existing_chunk_hashes]

        # embed chunks and nodes (if needed)
        node_artifacts: list[Artifact] = []
        if self.embed_nodes:
            chunks = embed_artifacts(self.embedder, chunks)
            node_artifacts = [node.to_artifact() for node in nodes_to_insert]
            node_artifacts = embed_artifacts(self.embedder, node_artifacts)

        # insert node artifacts in vector store (if exists)
        if self.vector_store is not None and len(node_artifacts) > 0:
            self.vector_store.insert(node_artifacts)
        else:
            # setup node embeddings for graph store
            self._transfer_embeddings_to_nodes(node_artifacts, nodes_to_insert)

        # upsert chunks, nodes, and relations to graph store
        if len(chunks) > 0:
            self.graph_store.upsert_artifacts(chunks)
        if len(node_artifacts) > 0:
            self.graph_store.upsert_nodes(nodes_to_insert)
        if len(relations_to_insert) > 0:
            self.graph_store.upsert_relations(relations_to_insert)

        # refresh schema if needed
        if self.graph_store.supports_structured_query:
            self.graph_store.get_schema(refresh=True)

        return chunks

    @override
    async def _ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        chunks = await self._ainsert_chunks(artifacts, **kwargs)
        for chunk in chunks:
            self.struct.add_artifact(chunk.id)

    async def _ainsert_chunks(self, chunks: list[Artifact], **kwargs) -> list[Artifact]:
        if len(chunks) == 0:
            return chunks

        # run transformations on chunks and extract triplets
        chunks = await arun_transformations(
            chunks,
            self.graph_extractors,
            cache=self.cache,
            cache_collection=self.cache_collection
        )
        nodes_to_insert, relations_to_insert = self._extract_triplets(chunks)

        # filter out duplicate nodes
        existing_nodes = await self.graph_store.aget(ids=list({node.id for node in nodes_to_insert}))
        existing_node_ids = {node.id for node in existing_nodes}
        del existing_nodes
        nodes_to_insert = [node for node in nodes_to_insert if node.id not in existing_node_ids]

        # filter out duplicate chunks
        existing_chunks = await self.graph_store.aget_artifacts([chunk.id for chunk in chunks])
        existing_chunk_hashes = [chunk.get_hash() for chunk in existing_chunks]
        del existing_chunks
        chunks = [chunk for chunk in chunks if chunk.get_hash() not in existing_chunk_hashes]

        # embed chunks and nodes (if needed)
        node_artifacts: list[Artifact] = []
        if self.embed_nodes:
            chunks = await aembed_artifacts(self.embedder, chunks)
            node_artifacts = [node.to_artifact() for node in nodes_to_insert]
            node_artifacts = await aembed_artifacts(self.embedder, node_artifacts)

        # insert node artifacts in vector store (if exists)
        if self.vector_store is not None and len(node_artifacts) > 0:
            await self.vector_store.ainsert(node_artifacts)
        else:
            # setup node embeddings for graph store
            self._transfer_embeddings_to_nodes(node_artifacts, nodes_to_insert)

        # upsert chunks, nodes, and relations to graph store
        if len(chunks) > 0:
            await self.graph_store.aupsert_artifacts(chunks)
        if len(nodes_to_insert) > 0:
            await self.graph_store.aupsert_nodes(nodes_to_insert)
        if len(relations_to_insert) > 0:
            await self.graph_store.aupsert_relations(relations_to_insert)

        # refresh schema if needed
        if self.graph_store.supports_structured_query:
            await self.graph_store.aget_schema(refresh=True)

        return chunks

    def _delete(self, artifact_id: str, **kwargs) -> None:
        self.graph_store.delete(ids=[artifact_id], **kwargs)
        self.struct.delete_artifact(artifact_id)

    @override
    async def _adelete(self, artifact_id: str, **kwargs) -> None:
        await self.graph_store.adelete(ids=[artifact_id], **kwargs)
        self.struct.delete_artifact(artifact_id)

    def get_ref_ids(self) -> list[str]:
        return []

    def get_artifact_ids(self) -> list[str]:
        return self.struct.artifact_ids

    def _extract_triplets(self, chunks: list[Artifact]) -> tuple[list[GraphNode], list[GraphRelation]]:
        # ensure all chunks have nodes and/or relations in metadata
        assert all(
            chunk.metadata.get(GRAPH_NODES_KEY) is not None
            or chunk.metadata.get(GRAPH_RELATIONS_KEY) is not None
            for chunk in chunks
        )

        nodes_to_insert: list[GraphNode] = []
        relations_to_insert: list[GraphRelation] = []
        for chunk in chunks:
            # remove nodes and relations from metadata
            nodes: list[GraphNode] = chunk.metadata.pop(GRAPH_NODES_KEY)
            relations: list[GraphRelation] = chunk.metadata.pop(GRAPH_RELATIONS_KEY)

            # add source id to properties
            for node in nodes:
                node.properties[GRAPH_TRIPLET_SOURCE_KEY] = chunk.id
            for relation in relations:
                relation.properties[GRAPH_TRIPLET_SOURCE_KEY] = chunk.id

            # add nodes and relations to insert lists
            nodes_to_insert.extend(nodes)
            relations_to_insert.extend(relations)

        return nodes_to_insert, relations_to_insert

    def _transfer_embeddings_to_nodes(
        self,
        artifacts: list[Artifact],
        nodes: list[GraphNode]
    ) -> None:
        for idx, node in enumerate(nodes):
            node_artifact = artifacts[idx]
            if node_artifact.embedding is not None:
                node.embedding = node_artifact.embedding.copy()
                node_artifact.embedding = None