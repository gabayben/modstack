from modstack.commands import Command
from modstack.typing import Utf8Artifact

class ClassifyLanguages(Command[list[Utf8Artifact]]):
    artifacts: list[Utf8Artifact]

    @classmethod
    def name(cls) -> str:
        return 'classify_languages'