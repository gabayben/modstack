from modstack.core import module

@module
def default_triplet_parser(
    response: str,
    max_length: int = 128,
    **kwargs
) -> tuple[str, str, str]:
    pass