from dataclasses import dataclass
from typing import Optional

from modstack.data.stores import ArtifactStore, InjestionCache, KVArtifactStore
from modstack.data.stores import GraphStore, SimpleGraphStore
from modstack.data.stores import SimpleKVStore
from modstack.data.stores.vector import SimpleVectorStore, VectorStore

@dataclass
class _Settings:
    _artifact_store: Optional[ArtifactStore] = None
    _graph_store: Optional[GraphStore] = None
    _vector_store: Optional[VectorStore] = None
    _ingestion_cache: Optional[InjestionCache] = None

    @property
    def artifact_store(self) -> ArtifactStore:
        return self._artifact_store

    @artifact_store.setter
    def artifact_store(self, artifact_store: ArtifactStore) -> None:
        self._artifact_store = artifact_store

    @property
    def graph_store(self) -> GraphStore:
        return self._graph_store

    @graph_store.setter
    def graph_store(self, graph_store: GraphStore) -> None:
        self._graph_store = graph_store

    @property
    def vector_store(self) -> VectorStore:
        return self._vector_store

    @vector_store.setter
    def vector_store(self, vector_store: VectorStore) -> None:
        self._vector_store = vector_store

    @property
    def ingestion_cache(self) -> InjestionCache:
        return self._ingestion_cache

    @ingestion_cache.setter
    def ingestion_cache(self, ingestion_cache: InjestionCache) -> None:
        self._ingestion_cache = ingestion_cache

_kvstore = SimpleKVStore()
Settings = _Settings(
    _artifact_store=KVArtifactStore(_kvstore),
    _graph_store=SimpleGraphStore(),
    _vector_store=SimpleVectorStore(),
    _ingestion_cache=InjestionCache(_kvstore)
)