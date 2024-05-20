from modstack.contracts import Contract
from modstack.typing import Utf8Artifact

class CleanText(Contract):
    artifacts: list[Utf8Artifact]

    @classmethod
    def name(cls) -> str:
        return 'clean_text'

class SplitText(Contract[list[Utf8Artifact]]):
    artifacts: list[Utf8Artifact]