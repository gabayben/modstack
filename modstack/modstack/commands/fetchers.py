from modstack.core import Command
from modstack.typing import ByteStream

class FetchFromLinks(Command[list[ByteStream]]):
    urls: list[str]