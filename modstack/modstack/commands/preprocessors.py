from modstack.commands import Command
from modstack.typing import Utf8Artifact

class CleanText(Command[list[Utf8Artifact]]):
    artifacts: list[Utf8Artifact]

class SplitText(Command[list[Utf8Artifact]]):
    artifacts: list[Utf8Artifact]