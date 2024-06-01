import logging
from typing import Any, ClassVar

from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML, RendererProtocol
from mdit_plain.renderer import RendererPlain

from modstack.core.modules import Modules
from modstack.core.typing import TextArtifact, Utf8Artifact
from modstack.core.utils.dicts import normalize_metadata
from modstack.core.utils.func import tzip
from modstack.markdown import MdItToText, RendererType

logger = logging.getLogger(__name__)

class MdIt(Modules.Sync[MdItToText, list[Utf8Artifact]]):
    renderers: ClassVar[dict[RendererType, Any]] = {
        'Plain': RendererPlain,
        'Html': RendererHTML
    }

    def _invoke(self, data: MdItToText, **kwargs) -> list[Utf8Artifact]:
        metadata = normalize_metadata(data.metadata, len(data.sources))
        results: list[TextArtifact] = []

        renderer: RendererProtocol = self.renderers[data.renderer_type]()
        parser = MarkdownIt(
            renderer_cls=lambda _: renderer,
            config=data.config,
            options_update=data.options_update
        )
        parser.enable(data.features, ignoreInvalid=data.ignore_invalid_features)

        for source, md in tzip(data.sources, metadata):
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