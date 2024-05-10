import logging
from typing import Any, ClassVar

from modstack.commands import FromTextFile
from modstack.core import Module, command
from modstack.typing import ArtifactSource, TextArtifact
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import zip2

logger = logging.getLogger(__name__)

class TextConverter(Module):
    known_html_extractors: ClassVar[list[str]] = [
        'DefaultExtractor',
        'ArticleExtractor',
        'ArticleSentencesExtractor',
        'LargestContentExtractor',
        'CanolaExtractor',
        'KeepEverythingExtractor',
        'NumWordsRulesExtractor'
    ]

    @command(FromTextFile)
    def from_text_file(
        self,
        sources: list[ArtifactSource],
        metadata: dict[str, Any] | list[dict[str, Any]] | None = None,
        **kwargs
    ) -> list[TextArtifact]:
        metadata = normalize_metadata(metadata, len(sources))
        results: list[TextArtifact] = []

        for source, md in zip2(sources, metadata):
            try:
                results.append(TextArtifact.from_source(source, md))
            except Exception as e:
                logger.warning(f'Could not read {source}. Skipping it. Error: {e}.')

        return results