from typing import ClassVar, Optional

from modstack.ai import LLMPrompt
from modstack.artifacts import Artifact, ArtifactSource
from modstack.artifacts.messages import MessageArtifact
from modstack.data.ingest import IngestFileType, email_partitioner, html_partitioner, text_partitioner
from modstack.modules import Module, ModuleLike, Modules, coerce_to_module, module

PARTITION_DETECTOR_SYSTEM_PROMPT = ''

@module
def _partition_detector(source: ArtifactSource) -> str:
    pass

class LLMPartitionDetector(Modules.Sync[Artifact, str]):
    def __init__(
        self,
        llm: Module[LLMPrompt, list[MessageArtifact]],
        system_prompt: Optional[str] = None
    ):
        self.llm = llm
        self.system_prompt: str = system_prompt or PARTITION_DETECTOR_SYSTEM_PROMPT

    def _invoke(self, artifact: Artifact, **kwargs) -> str:
        pass

class Partitioner(Modules.Sync[ArtifactSource, list[Artifact]]):
    detector: ClassVar[Module[ArtifactSource, str]] = _partition_detector
    fallback_detector: Optional[Module[Artifact, str]]
    partitioners: dict[str, Module[ArtifactSource, list[Artifact]]]

    def __init__(
        self,
        fallback_detector: Optional[ModuleLike[Artifact, str]] = None,
        custom_partitioners: Optional[dict[str, ModuleLike[ArtifactSource, list[Artifact]]]] = None,
        **kwargs
    ):
        fallback_detector = coerce_to_module(fallback_detector) if fallback_detector else None

        partitioners = {
            IngestFileType.EMAIL: email_partitioner,
            IngestFileType.HTML: html_partitioner,
            IngestFileType.TEXT: text_partitioner
        }

        if custom_partitioners:
            for file_type, partitioner in custom_partitioners.items():
                partitioners[file_type] = coerce_to_module(partitioner)

        super().__init__(
            fallback_detector=fallback_detector,
            partitioners=partitioners,
            **kwargs
        )

    def _invoke(self, source: ArtifactSource, **kwargs) -> list[Artifact]:
        pass