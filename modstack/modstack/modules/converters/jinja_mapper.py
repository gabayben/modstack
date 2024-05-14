from typing import Any, cast

from jinja2 import Template, meta

from modstack.commands import JinjaMapping, command
from modstack.modules import Module

class JinjaMapper(Module):
    def __init__(self, template: str, **kwargs):
        super().__init__(**kwargs)
        self.template = Template(template)
        ast = self.template.environment.parse(template)
        template_variables = meta.find_undeclared_variables(ast)
        self.context_variables = {v: (Any, None) for v in template_variables}

    @command(JinjaMapping)
    def map(self, context: Any, **kwargs) -> Any:
        return cast(Any, self.template.render(context))