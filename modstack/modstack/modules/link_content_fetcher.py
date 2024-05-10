from modstack.commands import FetchFromLinks
from modstack.core import Module, command
from modstack.typing import ByteStream

class LinkContentFetcher(Module):
    @command(FetchFromLinks)
    def fetch(self, urls: list[str], **kwargs) -> list[ByteStream]:
        pass