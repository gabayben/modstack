from dataclasses import dataclass
from typing import Optional

from modstack.stores.artifact import ArtifactStore, KVArtifactStore
from modstack.stores.graph import GraphStore
from modstack.stores.index import IndexStore, KVIndexStore
from modstack.stores.keyvalue import KVStore, SimpleKVStore
from modstack.stores.vector import VectorStore

@dataclass
class _Settings:
    _kvstore: Optional[KVStore] = None
    _artifact_store: Optional[ArtifactStore] = None
    _index_store: Optional[IndexStore] = None
    _graph_store: Optional[GraphStore] = None
    _vector_store: Optional[VectorStore] = None

    @property
    def kvstore(self) -> KVStore:
        return self._kvstore

    @kvstore.setter
    def kvstore(self, kvstore: KVStore) -> None:
        self._kvstore = kvstore

    @property
    def artifact_store(self) -> ArtifactStore:
        return self._artifact_store

    @artifact_store.setter
    def artifact_store(self, artifact_store: ArtifactStore) -> None:
        self._artifact_store = artifact_store

    @property
    def index_store(self) -> IndexStore:
        return self._index_store

    @index_store.setter
    def index_store(self, index_store: IndexStore) -> None:
        self._index_store = index_store

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

_kvstore = SimpleKVStore()
Settings = _Settings(
    _kvstore=_kvstore,
    _artifact_store=KVArtifactStore(_kvstore),
    _index_store=KVIndexStore(_kvstore)
)