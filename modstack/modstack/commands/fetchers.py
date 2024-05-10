from modstack.commands import Command
from modstack.typing import ByteStream

class FetchFromLinks(Command[list[ByteStream]]):
    urls: list[str]