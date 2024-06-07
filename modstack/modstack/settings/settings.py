from dataclasses import dataclass
from typing import Optional

from modstack.stores.artifact import ArtifactStore, KVArtifactStore
from modstack.stores.graph import GraphStore, SimpleGraphStore
from modstack.stores.index import IndexStore, KVIndexStore
from modstack.stores.keyvalue import KVStore, SimpleKVStore
from modstack.stores.vector import SimpleVectorStore, VectorStore

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
        if isinstance(self.artifact_store, KVArtifactStore):
            self.artifact_store = KVArtifactStore(self._kvstore)
        if isinstance(self.index_store, KVIndexStore):
            self.index_store = KVIndexStore(self._kvstore)

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
    _index_store=KVIndexStore(_kvstore),
    _graph_store=SimpleGraphStore(),
    _vector_store=SimpleVectorStore()
)