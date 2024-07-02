from typing import NamedTuple

from pydantic import Field

from modstack.artifacts import Artifact
from modstack.typing import Schema

class ZeroShotClassifierInput(Schema):
    artifact: Artifact
    labels: list[str] = Field(default_factory=list)

class PredictedLabel(NamedTuple):
    label: str
    score: float