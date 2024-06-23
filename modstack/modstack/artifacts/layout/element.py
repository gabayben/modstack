from abc import ABC
from enum import StrEnum
from typing import Any

from modstack.artifacts import Utf8Artifact

class ElementType(StrEnum):
    TITLE = 'Title'
    TEXT = 'Text'
    NARRATIVE_TEXT = 'NarrativeText'
    BULLETED_TEXT = 'BulletedText'

class ElementSourceMetadata(dict[str, Any]):
    pass

class ElementCoordinatesMetadata(dict[str, Any]):
    pass

class ElementMetadata(dict[str, Any]):
    pass

class Element(Utf8Artifact, ABC):
    pass