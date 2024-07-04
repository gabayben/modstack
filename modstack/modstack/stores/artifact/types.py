from dataclasses import dataclass, field
from typing import Any

from dataclasses_json import DataClassJsonMixin

@dataclass
class RefArtifactInfo(DataClassJsonMixin):
    artifact_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)