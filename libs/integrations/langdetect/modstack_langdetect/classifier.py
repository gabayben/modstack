import logging

import langdetect

from modstack.contracts import ClassifyLanguages
from modstack.modules import Modules
from modstack.typing import Utf8Artifact

logger = logging.getLogger(__name__)

class LangDetectClassifier(Modules.Sync[ClassifyLanguages, list[Utf8Artifact]]):
    def __init__(self, languages: list[str] | None = None):
        super().__init__()
        self.languages = languages or ['en']

    def _invoke(self, data: ClassifyLanguages) -> list[Utf8Artifact]:
        for artifact in data.artifacts:
            detected_language = self._detect_language(artifact)
            if detected_language in self.languages:
                artifact.metadata['language'] = detected_language
            else:
                artifact.metadata['language'] = 'unmatched'
        return data.artifacts

    def _detect_language(self, artifact: Utf8Artifact) -> str | None:
        try:
            detected_language = langdetect.detect(str(artifact))
        except langdetect.LangDetectException as e:
            logger.warning(f'LangDetect cannot detect the language of artifact with id: {artifact.id}. Error: {e}.')
            detected_language = None
        return detected_language