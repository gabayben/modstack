from dataclasses import dataclass
from typing import Any, Optional

@dataclass(kw_only=True)
class GraphNodeQuery:
    ids: Optional[list[str]] = None
    properties: Optional[dict[str, Any]] = None

@dataclass(kw_only=True)
class GraphTripletQuery:
    ids: Optional[list[str]] = None
    entity_names: Optional[list[str]] = None
    relation_names: Optional[list[str]] = None
    sources: Optional[list[str]] = None
    targets: Optional[list[str]] = None
    properties: Optional[dict[str, Any]] = None