from collections import defaultdict
import logging
from typing import Type, override

import langdetect
from pydantic import BaseModel

from modstack.artifacts import Utf8Artifact
from modstack.modules import Modules
from modstack.utils.serialization import create_model

logger = logging.getLogger(__name__)

class LangDetectRouter(Modules.Sync[list[Utf8Artifact], dict[str, list[Utf8Artifact]]]):
    def __init__(self, languages: list[str] | None = None):
        super().__init__()
        languages = languages or ['en']
        self.languages = languages

    def _invoke(self, artifacts: list[Utf8Artifact], **kwargs) -> dict[str, list[Utf8Artifact]]:
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

    @override
    def output_schema(self) -> Type[BaseModel]:
        return create_model(
            'RouteByLanguageOutput',
            unmatched=(list[Utf8Artifact], []),
            **{language: (list[Utf8Artifact], []) for language in self.languages}
        )