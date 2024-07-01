from dataclasses import dataclass
from typing import Optional

from modstack.data.stores import ArtifactStore, IndexStore, InjestionCache, KVArtifactStore, KVIndexStore, KVStore
from modstack.data.stores import GraphStore, SimpleGraphStore
from modstack.data.stores import SimpleKVStore
from modstack.data.stores.vector import SimpleVectorStore, VectorStore

@dataclass
class _Settings:
    _kvstore: Optional[KVStore] = None
    _artifact_store: Optional[ArtifactStore] = None
    _index_store: Optional[IndexStore] = None
    _graph_store: Optional[GraphStore] = None
    _vector_store: Optional[VectorStore] = None
    _ingestion_cache: Optional[InjestionCache] = None

    @property
    def kvstore(self) -> KVStore:
        if self._kvstore is None:
            self._kvstore = SimpleKVStore()
        return self._kvstore

    @kvstore.setter
    def kvstore(self, kvstore: Optional[KVStore]) -> None:
        self._kvstore = kvstore

    @property
    def artifact_store(self) -> ArtifactStore:
        if self._artifact_store is None:
            self._artifact_store = KVArtifactStore(self.kvstore)
        return self._artifact_store

    @artifact_store.setter
    def artifact_store(self, artifact_store: Optional[ArtifactStore]) -> None:
        self._artifact_store = artifact_store

    @property
    def index_store(self) -> IndexStore:
        if self._index_store is None:
            self._index_store = KVIndexStore(self.kvstore)
        return self._index_store

    @index_store.setter
    def index_store(self, index_store: Optional[IndexStore]) -> None:
        self._index_store = index_store

    @property
    def graph_store(self) -> GraphStore:
        if self._graph_store is None:
            self._graph_store = SimpleGraphStore()
        return self._graph_store

    @graph_store.setter
    def graph_store(self, graph_store: Optional[GraphStore]) -> None:
        self._graph_store = graph_store

    @property
    def vector_store(self) -> VectorStore:
        if self._vector_store is None:
            self._vector_store = SimpleVectorStore()
        return self._vector_store

    @vector_store.setter
    def vector_store(self, vector_store: Optional[VectorStore]) -> None:
        self._vector_store = vector_store

    @property
    def ingestion_cache(self) -> InjestionCache:
        if self._ingestion_cache is None:
            self._ingestion_cache = InjestionCache(self.kvstore)
        return self._ingestion_cache

    @ingestion_cache.setter
    def ingestion_cache(self, ingestion_cache: Optional[InjestionCache]) -> None:
        self._ingestion_cache = ingestion_cache

_kvstore = SimpleKVStore()
Settings = _Settings(_kvstore=_kvstore)