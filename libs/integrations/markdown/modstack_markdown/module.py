import logging
from typing import Any, ClassVar, Mapping

from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML, RendererProtocol
from markdown_it.utils import PresetType
from mdit_plain.renderer import RendererPlain

from modstack.contracts import HtmlToText
from modstack.modules import Modules
from modstack.typing import ArtifactSource, TextArtifact, Utf8Artifact
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import tzip
from modstack_markdown import MdItToText, RendererType

logger = logging.getLogger(__name__)

class _Markdown:
    renderers: ClassVar[dict[RendererType, Any]] = {
        'Plain': RendererPlain,
        'Html': RendererHTML
    }

    def _to_text(
        self,
        sources: list[ArtifactSource],
        metadata: dict[str, Any] | list[dict[str, Any]] | None = None,
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

class Markdown:
    class ToText(Modules.Sync[MdItToText, list[Utf8Artifact]], _Markdown):
        def _invoke(self, data: MdItToText) -> list[Utf8Artifact]:
            return self._to_text(**dict(data))

    class HtmlToText(Modules.Sync[HtmlToText, list[Utf8Artifact]], _Markdown):
        def _invoke(self, data: HtmlToText) -> list[Utf8Artifact]:
            return self._to_text(**dict(data), renderer_type='Html')