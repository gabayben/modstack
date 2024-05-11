from modstack.commands import Command
from modstack.typing import TextArtifact

class SplitText(Command[list[TextArtifact]]):
    artifacts: list[TextArtifact]