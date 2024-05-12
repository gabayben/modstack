from typing import Any

from modstack.commands import GenerateText, TextGeneration, command
from modstack.modules import Module

class OllamaTextGenerator(Module):
    def __init__(
        self,
        url: str = 'http://localhost:11434/api/generate',
        model: str = 'orca-mini'
    ):
        super().__init__()
        self.url = url
        self.model = model

    @command(GenerateText, name='generate_text')
    def generate(
        self,
        prompt: str,
        generation_args: dict[str, Any] | None = None,
        **kwargs
    ) -> TextGeneration:
        pass