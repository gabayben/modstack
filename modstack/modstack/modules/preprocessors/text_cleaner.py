from copy import deepcopy
from itertools import chain
import logging
import re
from typing import Generator

from modstack.artifacts import TextArtifact, Utf8Artifact
from modstack.modules import Modules
from modstack.utils.func import tintersection, tmap, tpartial, treduce

logger = logging.getLogger(__name__)

class TextCleaner(Modules.Sync[list[Utf8Artifact], list[Utf8Artifact]]):
    def __init__(
        self,
        remove_extra_whitespaces: bool = True,
        remove_empty_lines: bool = True,
        remove_substrings: list[str] | None = None,
        remove_regex: str | None = None,
        remove_repeated_substrings: bool = False
    ):
        super().__init__()
        self.remove_extra_whitespaces = remove_extra_whitespaces
        self.remove_empty_lines = remove_empty_lines
        self.remove_substrings = remove_substrings
        self.remove_regex = remove_regex
        self.remove_repeated_substrings = remove_repeated_substrings

    def _invoke(self, artifacts: list[Utf8Artifact], **kwargs) -> list[Utf8Artifact]:
        cleaned_artifacts: list[TextArtifact] = []

        for artifact in artifacts:
            try:
                text = artifact.to_utf8()
            except UnicodeDecodeError as e:
                raise ValueError(f'Could not retrieve UTF-8 content from artifact with id: {artifact.id}. Error: {e}.') from e
            if self.remove_extra_whitespaces:
                text = self._remove_extra_whitespaces(text)
            if self.remove_empty_lines:
                text = self._remove_empty_lines(text)
            if self.remove_substrings:
                text = self._remove_substrings(text)
            if self.remove_regex:
                text = self._remove_regex(text)
            if self.remove_repeated_substrings:
                text = self._remove_repeated_substrings(text)
            cleaned_artifacts.append(TextArtifact(text, metadata={**deepcopy(artifact.metadata), 'cleaned': True}))

        return cleaned_artifacts

    def _remove_extra_whitespaces(self, text: str) -> str:
        return re.sub(r'\s\s+', ' ', text).strip()

    def _remove_empty_lines(self, text: str) -> str:
        lines = text.split('\n')
        non_empty_lines = filter(lambda line: line.strip() != '', lines)
        return '\n'.join(non_empty_lines)

    def _remove_substrings(self, text: str) -> str:
        for substring in self.remove_substrings:
            text = text.replace(substring, '')
        return text

    def _remove_regex(self, text: str) -> str:
        return re.sub(self.remove_regex, '', text).strip()

    def _remove_repeated_substrings(self, text: str) -> str:
        return self._find_and_remove_header_footer(text, 300, 1, 1)

    def _find_and_remove_header_footer(
        self,
        text: str,
        n_chars: int,
        n_first_pages_to_ignore: int,
        n_last_pages_to_ignore: int
    ) -> str:
        pages = text.split('\f')

        start_of_pages = [p[:n_chars] for p in pages[n_first_pages_to_ignore:-n_last_pages_to_ignore]]
        found_header = self._find_longest_common_ngram(start_of_pages)
        if found_header:
            pages = [page.replace(found_header, '') for page in pages]

        last_of_pages = [p[-n_chars:] for p in pages[n_first_pages_to_ignore:-n_last_pages_to_ignore]]
        found_footer = self._find_longest_common_ngram(last_of_pages)
        if found_footer:
            pages = [page.replace(found_footer, '') for page in pages]

        logger.debug(f"Removed header {found_header} and footer {found_footer} in artifact.")
        return '\f'.join(pages)

    def _find_longest_common_ngram(
        self,
        sequences: list[str],
        min_ngram: int = 3,
        max_ngram: int = 30
    ) -> str:
        sequences = [s for s in sequences if s]
        if not sequences:
            return ''
        seqs_ngrams = tmap(tpartial(self._all_ngrams, min_ngram=min_ngram, max_ngram=max_ngram), sequences)
        intersection = treduce(tintersection, seqs_ngrams)
        longest = max(intersection, key=len, default='')
        return longest if longest.strip() else ''

    def _all_ngrams(
        self,
        sequence: str,
        min_ngram: int,
        max_ngram: int | None
    ) -> set[str]:
        lengths = range(min_ngram, max_ngram) if max_ngram else range(min_ngram, len(sequence))
        ngrams = tmap(tpartial(self._ngram, sequence), lengths)
        return set(chain.from_iterable(ngrams))

    def _ngram(self, sequence: str, n: int) -> Generator[str, None, None]:
        sequence = sequence.replace('\n', ' \n')
        sequence = sequence.replace('\t', ' \t')
        words = sequence.split(' ')
        return (
            ' '.join(words[i: i + n]).replace(' \n', '\n').replace(' \t', '\t')
            for i in range(len(words) - n + 1)
        )