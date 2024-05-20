from modstack.contracts import Contract
from modstack.typing import Utf8Artifact

class CleanText(Contract):
    artifacts: list[Utf8Artifact]

class SplitText(Contract):
    artifacts: list[Utf8Artifact]