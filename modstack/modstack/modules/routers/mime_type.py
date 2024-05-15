from collections import defaultdict
import re
from re import Pattern

from modstack.containers import feature

from modstack.contracts import RouteByMimeType
from modstack.modules import Module
from modstack.typing import Artifact, ArtifactSource, StrictArtifactSource
from modstack.utils.serialization import create_model

class MimeTypeRouter(Module):
    def __init__(self, mime_types: list[str]):
        super().__init__()
        if not mime_types:
            raise ValueError('The list of mime types cannot be empty.')
        self.mime_type_patterns: list[Pattern] = []
        for mime_type in mime_types:
            if not _is_valid_mime_type_format(mime_type):
                raise ValueError(f"Invalid mime type or regex pattern: '{mime_type}'.")
            self.mime_type_patterns.append(re.compile(mime_type))
        self.set_output_schema(
            RouteByMimeType.name(),
            create_model(
                'RouteByMimeTypeOutput',
                unclassified=(list[StrictArtifactSource], []),
                **{mime_type: (list[StrictArtifactSource], []) for mime_type in mime_types}
            )
        )
        self.mime_types = mime_types

    @feature(name=RouteByMimeType.name(), ignore_output_schema=True)
    def route(self, sources: list[ArtifactSource], **kwargs) -> dict[str, list[StrictArtifactSource]]:
        sources_by_mime_type: defaultdict[str, list[StrictArtifactSource]] = defaultdict(list)
        for source in sources:
            mime_type = Artifact.get_mime_type(source)
            matched = False
            if mime_type:
                for pattern in self.mime_type_patterns:
                    if pattern.fullmatch(mime_type):
                        sources_by_mime_type[pattern.pattern].append(source)
                        matched = True
                        break
            if not matched:
                sources_by_mime_type['unclassified'].append(source)
        return sources_by_mime_type

def _is_valid_mime_type_format(mime_type: str) -> bool:
    try:
        re.compile(mime_type)
        return True
    except re.error:
        return False