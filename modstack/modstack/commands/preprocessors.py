from modstack.commands import Command
from modstack.typing import Artifact, TextArtifact

class CleanText(Command[list[TextArtifact]]):
    artifacts: list[Artifact]

class SplitText(Command[list[TextArtifact]]):
    artifacts: list[Artifact]