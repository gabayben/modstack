from modstack.commands import FetchFromLinks, command
from modstack.modules import Module
from modstack.typing import ByteStream

class LinkContentFetcher(Module):
    @command(FetchFromLinks)
    def fetch(self, urls: list[str], **kwargs) -> list[ByteStream]:
        pass