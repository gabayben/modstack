from typing import Any, Mapping

def mapping_to_str(
    obj: Mapping[str, Any | None],
    exclude: list[str] = []
) -> str:
    text = ''
    for k, v in obj.items():
        if k not in exclude and v:
            text += f'\n{k}: {v}'
    return text.strip('\n')