from modstack.modules import LLMPrompt, PredictedLabel, ZeroShotClassifierInput
from modstack.artifacts import Artifact
from modstack.artifacts.messages import MessageArtifact
from modstack.core import Module

Embedder = Module[list[Artifact], list[Artifact]]
ZeroShotClassifier = Module[ZeroShotClassifierInput, list[PredictedLabel]]
LLM = Module[LLMPrompt, MessageArtifact]