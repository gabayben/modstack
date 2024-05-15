from typing import Any

from modstack.containers import feature_fn

from modstack.contracts.utils import ToTextArtifacts
from modstack.typing import TextArtifact
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import tzip

@feature_fn(name=ToTextArtifacts.name())
def to_text_artifacts(content: list[str], metadata: list[dict[str, Any]] | None = None) -> list[TextArtifact]:
    metadata = normalize_metadata(metadata or [], len(content))
    return [
        TextArtifact(text, metadata=metadata)
        for text, md in tzip(content, metadata)
    ]