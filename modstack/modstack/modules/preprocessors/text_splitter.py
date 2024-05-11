from builtins import UnicodeDecodeError
from copy import deepcopy
from typing import Any, Literal

from more_itertools import windowed

from modstack.commands import SplitText, command
from modstack.modules import Module
from modstack.typing import Artifact, TextArtifact

SplitBy = Literal['word', 'sentence', 'passage', 'page']
SPLIT_BY_MAPPING: dict[SplitBy, str] = {
    'word': ' ',
    'sentence': '.',
    'passage': '\n\n',
    'page': '\f'
}

class TextSplitter(Module):
    def __init__(
        self,
        split_by: SplitBy = 'word',
        split_length: int = 200,
        split_overlap: int = 0
    ):
        super().__init__()
        self.split_by = split_by
        if split_length <= 0:
            raise ValueError('split_length must be greater than 0.')
        self.split_length = split_length
        if split_overlap < 0:
            raise ValueError('split_overlap must be greater than or equal to 0.')
        self.split_overlap = split_overlap

    @command(SplitText)
    def split(self, artifacts: list[Artifact], **kwargs) -> list[TextArtifact]:
        split_artifacts: list[TextArtifact] = []
        for artifact in artifacts:
            try:
                units = self._split_into_units(artifact.to_utf8())
            except UnicodeDecodeError as e:
                raise ValueError(f'Unable to extract UTF-8 text from artifact with id: {artifact.id}. Error: {e}.') from e
            splits, splits_pages = self._concatenate_units(units)
            metadata = deepcopy(artifact.metadata)
            metadata['source_id'] = artifact.id
            split_artifacts += _create_artifacts_from_splits(splits, splits_pages, metadata)
        return split_artifacts

    def _split_into_units(self, text: str) -> list[str]:
        units = text.split(SPLIT_BY_MAPPING[self.split_by])
        for i in range(len(units) - 1):
            units[i] += self.split_by
        return units

    def _concatenate_units(self, elements: list[str]) -> tuple[list[str], list[int]]:
        splits: list[str] = []
        splits_pages: list[int] = []
        current_page = 1
        segments = windowed(elements, n=self.split_length, step=self.split_length - self.split_overlap)
        for segment in segments:
            current_units = [unit for unit in segment if unit is not None]
            text = ''.join(current_units)
            if len(text) > 0:
                splits.append(text)
                splits_pages.append(current_page)
                processed_units = current_units[: self.split_length - self.split_overlap]
                if self.split_by == '\f':
                    num_page_breaks = len(processed_units)
                else:
                    num_page_breaks = sum(processed_unit.count('\f') for processed_unit in processed_units)
                current_page += num_page_breaks
        return splits, splits_pages

def _create_artifacts_from_splits(
    splits: list[str],
    splits_pages: list[int],
    metadata: dict[str, Any]
) -> list[TextArtifact]:
    artifacts: list[TextArtifact] = []
    for i, split in splits:
        md = deepcopy(metadata)
        artifact = TextArtifact(split, metadata=md)
        artifact.metadata['page_number'] = splits_pages[i]
        artifacts.append(artifact)
    return artifacts