import logging
from typing import Any, ClassVar, Literal, Mapping, Optional

from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML, RendererProtocol
from markdown_it.utils import PresetType
from mdit_plain.renderer import RendererPlain

from modstack.artifacts import ArtifactSource, TextArtifact, Utf8Artifact
from modstack.modules import Modules
from modstack.typing import MetadataType
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import tzip

logger = logging.getLogger(__name__)

RendererType = Literal['Plain', 'Html']

class MdItConverter(Modules.Sync[list[ArtifactSource], list[Utf8Artifact]]):
    renderers: ClassVar[dict[RendererType, Any]] = {
        'Plain': RendererPlain,
        'Html': RendererHTML
    }

    def _invoke(
        self,
        sources: list[ArtifactSource],
        metadata: Optional[MetadataType] = None,
        renderer_type: RendererType = 'Plain',
        config: PresetType | str = 'commonmark',
        options_update: Mapping[str, Any] | None = None,
        features: list[str] = [],
        ignore_invalid_features: bool = False,
        **kwargs
    ) -> list[Utf8Artifact]:
        metadata = normalize_metadata(metadata, len(sources))
        results: list[TextArtifact] = []

        renderer: RendererProtocol = self.renderers[renderer_type]()
        parser = MarkdownIt(
            renderer_cls=lambda _: renderer,
            config=config,
            options_update=options_update
        )
        parser.enable(features, ignoreInvalid=ignore_invalid_features)

        for source, md in tzip(sources, metadata):
            try:
                artifact = TextArtifact.from_source(source, metadata=md)
            except Exception as e:
                logger.warning(f'Could not read {source}. Skipping it.')
                logger.exception(e)
                continue
            try:
                text = parser.render(artifact.to_utf8())
                results.append(TextArtifact(text, metadata=artifact.metadata))
            except Exception as e:
                logger.warning(f'Failed to extract text from {source}. Skipping it.')
                logger.exception(e)

        return results