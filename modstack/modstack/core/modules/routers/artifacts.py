from typing import Type

from jinja2 import TemplateError
from jinja2.nativetypes import NativeEnvironment
from pydantic import BaseModel

from modstack.core.modules import Modules
from modstack.core.typing import Artifact
from modstack.core.utils.serialization import create_model

class ArtifactRouter(Modules.Sync[list[Artifact], dict[str, list[Artifact]]]):
    def __init__(
        self,
        branches: dict[str, str],
        included_variables: list[str] | None = None
    ):
        super().__init__()
        self.branches = branches
        self.included_variables = included_variables

    def _invoke(self, artifacts: list[Artifact], **kwargs) -> dict[str, list[Artifact]]:
        unmatched_artifacts: list[Artifact] = []
        artifacts_by_branch: dict[str, list[Artifact]] = {branch: [] for branch in self.branches}
        env = NativeEnvironment()

        for artifact in artifacts:
            template_variables = {
                k: v
                for k, v in dict(artifact).items()
                if not self.included_variables or k in self.included_variables
            }
            matched = False
            for branch, condition in self.branches.items():
                try:
                    template = env.from_string(condition)
                    rendered = template.render(**template_variables)
                    if type(rendered) is not bool:
                        raise ValueError(f'Expected a boolean output. Got {rendered}.')
                    matched = rendered
                except Exception as e:
                    raise TemplateError(f'Error evaluating condition for {branch}: {e}.') from e
                else:
                    if matched:
                        artifacts_by_branch[branch].append(artifact)
            if not matched:
                unmatched_artifacts.append(artifact)

        return {'unmatched': unmatched_artifacts, **artifacts_by_branch}

    def output_schema(self) -> Type[BaseModel]:
        return create_model(
            'RouteArtifactsOutput',
            unmatched=(list[Artifact], []),
            **{key: (list[Artifact], []) for key in self.branches.keys()}
        )