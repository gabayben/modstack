from collections import defaultdict
import logging

import langdetect

from modstack.containers import feature
from modstack.contracts import RouteByLanguage
from modstack.modules import Module
from modstack.typing import Utf8Artifact
from modstack.utils.serialization import create_model

logger = logging.getLogger(__name__)

class LangDetectRouter(Module):
    def __init__(self, languages: list[str] | None = None):
        super().__init__()
        languages = languages or ['en']
        self.set_output_schema(
            RouteByLanguage.name(),
            create_model(
                'RouteByLanguageOutput',
                unmatched=(list[Utf8Artifact], []),
                **{language: (list[Utf8Artifact], []) for language in languages}
            )
        )
        self.languages = languages

    @feature(name=RouteByLanguage.name(), ignore_output_schema=True)
    def route(self, artifacts: list[Utf8Artifact], **kwargs) -> dict[str, list[Utf8Artifact]]:
        artifacts_by_language: defaultdict[str, list[Utf8Artifact]] = defaultdict(list)
        for artifact in artifacts:
            detected_language = self._detect_language(artifact)
            if detected_language in self.languages:
                artifacts_by_language[detected_language].append(artifact)
            else:
                artifacts_by_language['unmatched'].append(artifact)
        return artifacts_by_language

    def _detect_language(self, artifact: Utf8Artifact) -> str | None:
        try:
            detected_language = langdetect.detect(str(artifact))
        except langdetect.LangDetectException as e:
            logger.warning(f'LangDetect cannot detect the language of artifact with id: {artifact.id}. Error: {e}.')
            detected_language = None
        return detected_language