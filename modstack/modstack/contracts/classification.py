from modstack.contracts import Contract
from modstack.typing import Utf8Artifact

class ClassifyLanguages(Contract[list[Utf8Artifact]]):
    artifacts: list[Utf8Artifact]

    @classmethod
    def name(cls) -> str:
        return 'classify_languages'