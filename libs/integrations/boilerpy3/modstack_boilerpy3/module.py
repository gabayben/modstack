import logging
from typing import ClassVar

from boilerpy3 import extractors
from boilerpy3.extractors import Extractor

from modstack.modules import Modules
from modstack.typing import TextArtifact
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import tzip
from modstack_boilerpy3 import BoilerToText

logger = logging.getLogger(__name__)

class BoilerPy3(Modules.Sync[BoilerToText, list[TextArtifact]]):
    known_html_extractors: ClassVar[list[str]] = [
        'DefaultExtractor',
        'KeepEverythingExtractor',
        'ArticleExtractor',
        'ArticleSentencesExtractor',
        'LargestContentExtractor',
        'CanolaExtractor',
        'NumWordsRulesExtractor'
    ]

    def _invoke(self, data: BoilerToText, **kwargs) -> list[TextArtifact]:
        metadata = normalize_metadata(data.metadata, len(data.sources))
        results: list[TextArtifact] = []

        extractors_list = (
            list(dict.fromkeys([data.extractor_type, *self.known_html_extractors]))
            if data.try_others
            else [data.extractor_type]
        )

        for source, md in tzip(data.sources, metadata):
            try:
                artifact = TextArtifact.from_source(source, metadata=md)
            except Exception as e:
                logger.warning(f'Could not read {source}. Skipping it.')
                logger.exception(e)
                continue
            for extractor_name in extractors_list:
                extractor_cls = getattr(extractors, extractor_name)
                extractor: Extractor = extractor_cls(raise_on_failure=False)
                try:
                    text = extractor.get_content(artifact.to_utf8())
                    if text:
                        break
                except Exception as e:
                    if data.try_others:
                        logger.warning(f'Failed to extract using {extractor_name} from {source}. Trying next extractor.')
                        logger.exception(e)
            if not text:
                logger.warning(f'Failed to extract text using extractors {extractors_list}. Skipping it.')
                continue
            results.append(TextArtifact(text, metadata=artifact.metadata))

        return results