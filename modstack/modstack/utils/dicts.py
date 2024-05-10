from typing import Any

def normalize_metadata(
    metadata: dict[str, Any] | list[dict[str, Any]],
    sources_count: int
) -> list[dict[str, Any]]:
    if metadata is None:
        return [{}] * sources_count
    if isinstance(metadata, dict):
        return [metadata] * sources_count
    if isinstance(metadata, list):
        if sources_count != len(metadata):
            raise ValueError("The length of the metadata list must match the number of sources.")
        return metadata
    raise ValueError("metadata must be either None, a dictionary or a list of dictionaries.")