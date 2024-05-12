from modstack.commands import Command
from modstack.typing import Utf8Artifact

class ClassifyLanguages(Command[list[Utf8Artifact]]):
    artifacts: list[Utf8Artifact]