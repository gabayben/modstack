from pathlib import Path
from typing import Optional

from modstack.artifacts import ArtifactSource
from modstack.utils.paths import last_modified_date

def last_modified_date_from_source(
    source: ArtifactSource,
    date_from_artifact: bool = True
) -> Optional[str]:
    if isinstance(source, (str, Path)):
        return last_modified_date(source)
    return source.last_modified if date_from_artifact else None