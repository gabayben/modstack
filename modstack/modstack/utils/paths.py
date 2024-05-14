import mimetypes
from pathlib import Path

CUSTOM_MIME_TYPE_MAPPINGS: dict[str, str] = {
    '.markdown': 'llm/markdown',
    '.md': 'llm/markdown'
}

def get_mime_type(path: Path) -> str | None:
    extension = path.suffix.lower()
    mime_type = mimetypes.guess_type(path.as_posix())[0]
    return CUSTOM_MIME_TYPE_MAPPINGS.get(extension, mime_type)