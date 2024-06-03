from typing import Any, Type, override

from jinja2 import Template, meta
from pydantic import BaseModel

from modstack.core.modules import Modules
from modstack.core.modules.builders import PromptData
from modstack.core.utils.serialization import create_model

class PromptBuilder(Modules.Sync[PromptData, str]):
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
        self.template_variables = meta.find_undeclared_variables(ast)

    def _invoke(self, prompt: PromptData, **kwargs) -> str:
        variables = dict(prompt)
        missing_variables = [v for v in self.required_variables if v not in variables]
        if missing_variables:
            raise ValueError(f'Missing required input variables: {', '.join(missing_variables)}.')
        return self.template.render(variables)

    @override
    def input_schema(self) -> Type[BaseModel]:
        return create_model(
            self.get_name(suffix='Input'),
            **{
                k: (Any, ...)
                if k in self.required_variables
                else (Any, '')
                for k in self.template_variables
            }
        )