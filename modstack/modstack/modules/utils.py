from modstack.contracts.utils import ToTextArtifacts
from modstack.modules import module
from modstack.typing import TextArtifact
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import tzip

@module
def to_text_artifacts(data: ToTextArtifacts) -> list[TextArtifact]:
    metadata = normalize_metadata(data.metadata, len(data.content))
    artifacts: list[TextArtifact] = []
    for text, md in tzip(data.content, metadata):
        artifacts.append(TextArtifact(text, metadata=md))
    return artifacts