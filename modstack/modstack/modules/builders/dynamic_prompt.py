from typing import Any, Type, override

from jinja2 import Template, meta
from pydantic import BaseModel

from modstack.modules import Modules
from modstack.modules.builders import DynamicPromptData
from modstack.utils.serialization import create_model, from_parameters

class DynamicPromptBuilder(Modules.Sync[DynamicPromptData, str]):
    def __init__(self, runtime_variables: list[str] | None = None):
        super().__init__()
        self.runtime_variables = runtime_variables or []
        self.schema_fields = from_parameters(self.input_schema().parameters)
        self.runtime_fields = {v: (Any | None, None) for v in self.runtime_variables}

    def _invoke(self, data: DynamicPromptData, **kwargs) -> str:
        template_variables = data.template_variables or {}
        variables = data.model_extra or {}
        variables_combined = {**variables, **template_variables}

        if not variables_combined:
            raise ValueError(
                'No template variables were provided. '
                'Please provide template variables to enable prompt generation.'
            )

        template = self._validate_template(data.prompt_source, set(variables_combined.keys()))
        return template.render(variables_combined)

    def _validate_template(self, prompt_source: str, provided_variables: set[str]) -> Template:
        template = Template(prompt_source)
        ast = template.environment.parse(prompt_source)
        required_template_variables = meta.find_undeclared_variables(ast)
        filled_template_variables = required_template_variables.intersection(provided_variables)
        if len(filled_template_variables) != len(required_template_variables):
            raise ValueError(
                f'{self.__class__.__name__} requires specific template variables that are missing. '
                f'Required variables: {required_template_variables}. Only the following variables '
                f'were provided: {provided_variables}. Please provide all the required template variables.'
            )
        return template

    @override
    def input_schema(self) -> Type[BaseModel]:
        return create_model(
            'BuildDynamicPromptInput',
            **self.schema_fields,
            **self.runtime_fields
        )