from typing import Iterable, NotRequired, TypedDict

from modstack.artifacts import Artifact
from modstack.data import IngestConnector
from modstack.modules import Module, SerializableModule

class IngestFlowState(TypedDict):
    artifacts: NotRequired[list[Artifact]]

def ingest_flow(
    runner: Module[IngestConnector, Iterable[Artifact]],
    partitioner: Module[Artifact, list[Artifact]],
    reformatters: list[Module[list[Artifact], list[Artifact]]],
    writer: Module[list[Artifact], list[Artifact]]
) -> SerializableModule[IngestFlowState, IngestFlowState]:
    pass