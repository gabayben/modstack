import logging

import langdetect

from modstack.commands import ClassifyLanguages, command
from modstack.modules import Module
from modstack.typing import TextArtifact

logger = logging.getLogger(__name__)

class LangDetectClassifier(Module):
    def __init__(self, languages: list[str] | None = None):
        super().__init__()
        self.languages = languages or ['en']

    @command(ClassifyLanguages)
    def classify(self, artifacts: list[TextArtifact], **kwargs) -> list[TextArtifact]:
        for artifact in artifacts:
            detected_language = self._detect_language(artifact)
            if detected_language in self.languages:
                artifact.metadata['language'] = detected_language
            else:
                artifact.metadata['language'] = 'unmatched'
        return artifacts

    def _detect_language(self, artifact: TextArtifact) -> str | None:
        try:
            detected_language = langdetect.detect(str(artifact))
        except langdetect.LangDetectException as e:
            logger.warning(f'LangDetect cannot detect the language of artifact with id: {artifact.id}. Error: {e}.')
            detected_language = None
        return detected_language