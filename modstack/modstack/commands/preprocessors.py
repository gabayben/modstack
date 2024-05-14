from modstack.commands import Command
from modstack.typing import Utf8Artifact

class CleanText(Command[list[Utf8Artifact]]):
    artifacts: list[Utf8Artifact]

    @classmethod
    def name(cls) -> str:
        return 'clean_text'

class SplitText(Command[list[Utf8Artifact]]):
    artifacts: list[Utf8Artifact]

    @classmethod
    def name(cls) -> str:
        return 'split_text'