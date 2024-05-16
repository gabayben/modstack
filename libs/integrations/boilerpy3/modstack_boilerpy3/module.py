import logging
from typing import Any, ClassVar

from boilerpy3 import extractors
from boilerpy3.extractors import Extractor

from modstack.endpoints import endpoint
from modstack.modules import Module
from modstack.typing import ArtifactSource, TextArtifact
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import tzip
from modstack_boilerpy3 import ExtractorType

logger = logging.getLogger(__name__)

class BoilerPy3(Module):
    known_html_extractors: ClassVar[list[str]] = [
        'DefaultExtractor',
        'KeepEverythingExtractor',
        'ArticleExtractor',
        'ArticleSentencesExtractor',
        'LargestContentExtractor',
        'CanolaExtractor',
        'NumWordsRulesExtractor'
    ]

    @endpoint
    def html_to_text(
        self,
        sources: list[ArtifactSource],
        metadata: dict[str, Any] | list[dict[str, Any]] | None = None,
        extractor_type: ExtractorType = 'DefaultExtractor',
        try_others: bool = True,
        **kwargs
    ) -> list[TextArtifact]:
        metadata = normalize_metadata(metadata, len(sources))
        results: list[TextArtifact] = []

        extractors_list = (
            list(dict.fromkeys([extractor_type, *self.known_html_extractors]))
            if try_others
            else [extractor_type]
        )

        for source, md in tzip(sources, metadata):
            try:
                artifact = TextArtifact.from_source(source, metadata=md)
            except Exception as e:
                logger.warning(f'Could not read {source}. Skipping it. Error: {e}.')
                continue
            for extractor_name in extractors_list:
                extractor_cls = getattr(extractors, extractor_name)
                extractor: Extractor = extractor_cls(raise_on_failure=False)
                try:
                    text = extractor.get_content(artifact.to_utf8())
                    if text:
                        break
                except Exception as e:
                    if try_others:
                        logger.warning(f'Failed to extract using {extractor_name} from {source}. Trying next extractor. Error: {e}.')
            if not text:
                logger.warning(f'Failed to extract text using extractors {extractors_list}. Skipping it.')
                continue
            results.append(TextArtifact(text, metadata=artifact.metadata))

        return results