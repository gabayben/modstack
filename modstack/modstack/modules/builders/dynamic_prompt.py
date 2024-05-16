from typing import Any

from jinja2 import Template, meta

from modstack.endpoints import endpoint
from modstack.modules import Module
from modstack.utils.serialization import create_model, from_parameters

class DynamicPromptBuilder(Module):
    def __init__(self, runtime_variables: list[str] | None = None):
        super().__init__()
        self.runtime_variables = runtime_variables or []
        schema_fields = from_parameters(self.get_parameters('build'))
        runtime_fields = {v: (Any | None, None) for v in self.runtime_variables}
        self.set_input_schema(
            'build',
            create_model(
                'BuildDynamicPromptInput',
                **schema_fields,
                **runtime_fields
            )
        )

    @endpoint(ignore_input_schema=True)
    def build(
        self,
        prompt_source: str,
        template_variables: dict[str, Any] | None = None,
        **variables
    ) -> str:
        template_variables = template_variables or {}
        variables = variables or {}
        variables_combined = {**variables, **template_variables}

        if not variables_combined:
            raise ValueError(
                'No template variables were provided. '
                'Please provide template variables to enable prompt generation.'
            )

        template = self._validate_template(prompt_source, set(variables_combined.keys()))
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