from typing import Any, Mapping, Type
import uuid

def mapping_to_str(
    obj: Mapping[str, Any | None],
    exclude: list[str] = []
) -> str:
    text = ''
    for k, v in obj.items():
        if k not in exclude and v:
            text += f'\n{k}: {v}'
    return text.strip('\n')

def is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

def type_name(type_: Type) -> str:
    return f'{type_.__module__}.{type_.__name__}'

def truncate_text(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."