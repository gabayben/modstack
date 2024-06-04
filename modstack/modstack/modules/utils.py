from typing import Any, NamedTuple

from modstack.artifacts import TextArtifact
from modstack.modules import module
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import tzip

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