from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, Sequence, TypedDict

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

class VectorStoreQuery(TypedDict, total=False):
    ref_artifact_ids: Optional[list[str]]
    artifact_ids: Optional[list[str]]
    query: Optional[Artifact]
    query_embedding: Optional[Embedding]
    embedding_field: Optional[str]
    output_fields: Optional[list[str]]
    filters: Optional[MetadataFilters]
    mode: Optional[str]
    similarity_top_k: Optional[int]
    sparse_top_k: Optional[int]
    hybrid_top_k: Optional[int]
    mmr_threshold: Optional[float]

@dataclass(kw_only=True)
class VectorStoreQueryResult:
    artifacts: Optional[Sequence[Artifact]] = None
    ids: Optional[list[str]] = None
    similarities: Optional[list[float]] = None