from abc import ABC, abstractmethod
from typing import Any, Optional, override

from pydantic import Field

from modstack.artifacts import Artifact, TextArtifact
from modstack.typing import Embedding, Serializable

class GraphElement(Serializable, ABC):
    label: Optional[str] = Field(default=None, kw_only=True)
    properties: dict[str, Any] = Field(default_factory=dict, kw_only=True)

    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    def to_artifact(self) -> Artifact:
        return TextArtifact(
            str(self),
            id=self.id,
            name=self.label,
            metadata=self.properties
        )

class GraphNode(GraphElement, ABC):
    embedding: Optional[Embedding] = Field(default=None, kw_only=True)

    @override
    def to_artifact(self) -> Artifact:
        return TextArtifact(
            str(self),
            id=self.id,
            name=self.label,
            embedding=self.embedding,
            metadata=self.properties
        )

class EntityNode(GraphNode):
    name: str

    @property
    def id(self) -> str:
        return self.name.replace('"', ' ')

    def __str__(self) -> str:
        return self.name

    @override
    def to_artifact(self) -> Artifact:
        return TextArtifact(
            str(self),
            id=self.id,
            name=self.name,
            embedding=self.embedding,
            metadata=self.properties
        )

class ChunkNode(GraphNode):
    text: str
    id_: Optional[str] = Field(default=None, kw_only=True)

    @property
    def id(self) -> str:
        return self.id_ or str(hash(self.text))

    def __str__(self) -> str:
        return self.text

class GraphRelation(GraphElement):
    source: str
    target: str

    @property
    def id(self) -> str:
        return f'{self.source}->{self.target}'

    def __str__(self) -> str:
        return self.label or f'{self.source} to {self.target}'

GraphTriplet = tuple[GraphNode, GraphRelation, GraphNode]

class Graph(Serializable):
    nodes: dict[str, GraphNode] = Field(default_factory=dict)
    relations: dict[str, GraphRelation] = Field(default_factory=dict)
    triplets: set[tuple[str, str, str]] = Field(default_factory=set)