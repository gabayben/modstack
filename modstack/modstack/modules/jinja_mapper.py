from typing import Any, Generic, Type, cast

from jinja2 import Template, meta

from modstack.commands import JinjaMapping
from modstack.core import Module, command
from modstack.typing.vars import Out

class JinjaMapper(Module, Generic[Out]):
    def __init__(self, template: str, output_type: Type[Out], **kwargs):
        super().__init__(**kwargs)
        self.output_type = output_type
        self.template = Template(template)
        ast = self.template.environment.parse(template)
        template_variables = meta.find_undeclared_variables(ast)
        self.context_variables = {v: (Any, None) for v in template_variables}

    @command(JinjaMapping[Out])
    def map(self, context: Any, **kwargs) -> Out:
        return cast(Out, self.template.render(context))