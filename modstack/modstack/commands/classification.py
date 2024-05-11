from modstack.commands import Command
from modstack.typing import TextArtifact

class ClassifyLanguages(Command[list[TextArtifact]]):
    artifacts: list[TextArtifact]