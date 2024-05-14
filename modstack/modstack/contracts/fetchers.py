from modstack.contracts import Contract
from modstack.typing import ByteStream

class FetchFromLinks(Contract[list[ByteStream]]):
    urls: list[str]

    @classmethod
    def name(cls) -> str:
        return 'fetch_from_links'