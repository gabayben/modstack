from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, Sequence

from modstack.artifacts import Artifact
from modstack.typing import Embedding, MetadataFilter, MetadataFilterInfo, MetadataFilters, Serializable

class VectorStoreInfo(Serializable):
    content_info: str
    metadata_info: list[MetadataFilterInfo]

class VectorStoreQueryMode(StrEnum):
    DEFAULT = 'default'
    TEXT_SEARCH = 'text_search'
    SPARSE = 'sparse'
    HYBRID = 'hybrid'
    SEMANTIC_HYBRID = 'semantic_hybrid'
    MMR = 'mmr'
    LINEAR_REGRESSION = 'linear_regression'
    LOGISTIC_REGRESSION = 'logistic_regression'
    SVM = 'svm'

class VectorStoreQuerySpec(Serializable):
    query: str
    filters: list[MetadataFilter]
    top_k: Optional[int] = None

@dataclass(kw_only=True)
class VectorStoreQuery:
    ref_artifact_ids: Optional[list[str]] = None
    artifact_ids: Optional[list[str]] = None
    query: Optional[Artifact] = None
    query_embedding: Optional[Embedding] = None
    embedding_field: Optional[str] = None
    output_fields: Optional[list[str]] = None
    filters: Optional[MetadataFilters] = None
    mode: str = VectorStoreQueryMode.DEFAULT
    similarity_top_k: int = 1
    sparse_top_k: Optional[int] = None
    hybrid_top_k: Optional[int] = None
    mmr_threshold: Optional[float] = None

@dataclass(kw_only=True)
class VectorStoreQueryResult:
    artifacts: Optional[Sequence[Artifact]] = None
    ids: Optional[list[str]] = None
    similarities: Optional[list[float]] = None