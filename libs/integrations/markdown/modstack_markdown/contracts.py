from typing import Any, Literal, Mapping

from markdown_it.utils import PresetType
from pydantic import Field

from modstack.contracts import ToText

RendererType = Literal['Plain', 'Html']

class MdItToText(ToText):
    renderer_type: RendererType = Field(default='Plain')
    config: PresetType | str = 'commonmark'
    options_update: Mapping[str, Any] | None = None
    features: list[str] = Field(default_factory=list)
    ignore_invalid_features: bool = False