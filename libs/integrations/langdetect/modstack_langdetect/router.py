from collections import defaultdict
import logging

import langdetect

from modstack.commands import RouteByLanguage, command
from modstack.modules import Module
from modstack.typing import TextArtifact
from modstack.utils.serialization import create_model

logger = logging.getLogger(__name__)

class LangDetectRouter(Module):
    def __init__(self, languages: list[str] | None = None):
        super().__init__()
        languages = languages or ['en']
        self.set_output_schema(
            RouteByLanguage,
            create_model(
                'RouteByLanguageOutput',
                unmatched=(list[TextArtifact], []),
                **{language: (list[TextArtifact], []) for language in languages}
            )
        )
        self.languages = languages

    @command(RouteByLanguage, ignore_output_schema=True)
    def route(self, artifacts: list[TextArtifact], **kwargs) -> dict[str, list[TextArtifact]]:
        artifacts_by_language: defaultdict[str, list[TextArtifact]] = defaultdict(list)
        for artifact in artifacts:
            detected_language = self._detect_language(artifact)
            if detected_language in self.languages:
                artifacts_by_language[detected_language].append(artifact)
            else:
                artifacts_by_language['unmatched'].append(artifact)
        return artifacts_by_language

    def _detect_language(self, artifact: TextArtifact) -> str | None:
        text = str(artifact)
        try:
            detected_language = langdetect.detect(text)
        except langdetect.LangDetectException as e:
            logger.warning(f'LangDetect cannot detect the language of text: {text}. Error: {e}.')
            detected_language = None
        return detected_language