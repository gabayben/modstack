from typing import Any, NamedTuple

from modstack.core.artifacts import TextArtifact
from modstack.core.modules import module
from modstack.core.utils.dicts import normalize_metadata
from modstack.core.utils.func import tzip

class ToTextArtifacts(NamedTuple):
    content: list[str]
    metadata: list[dict[str, Any]] | dict[str, Any] | None = None

@module
def to_text_artifacts(data: ToTextArtifacts) -> list[TextArtifact]:
    metadata = normalize_metadata(data.metadata, len(data.content))
    artifacts: list[TextArtifact] = []
    for text, md in tzip(data.content, metadata):
        artifacts.append(TextArtifact(text, metadata=md))
    return artifacts