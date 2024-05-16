from typing import Any

from jinja2 import Template, meta

from modstack.endpoints import endpoint
from modstack.modules import Module
from modstack.utils.serialization import create_model

class PromptBuilder(Module):
    def __init__(
        self,
        template: str,
        required_variables: list[str] | None = None
    ):
        super().__init__()
        self._template_string = template
        self.template = Template(template)
        self.required_variables = required_variables or []
        ast = self.template.environment.parse(template)
        template_variables = meta.find_undeclared_variables(ast)
        self.set_input_schema(
            'build',
            create_model(
                'BuildPromptInput',
                **{
                    k: (Any, ...)
                    if k in self.required_variables
                    else (Any, '')
                    for k in template_variables
                }
            )
        )

    @endpoint(ignore_input_schema=True)
    def build(self, **variables) -> str:
        missing_variables = [v for v in self.required_variables if v not in variables]
        if missing_variables:
            raise ValueError(f'Missing required input variables: {', '.join(missing_variables)}.')
        return self.template.render(variables)