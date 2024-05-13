import inspect
from inspect import Parameter
from types import MappingProxyType
from typing import Any, Type

from pydantic import BaseModel

from modstack.constants import MODSTACK_FEATURE
from modstack.containers import Feature, FeatureNotFound

class Module:
    @property
    def features(self) -> dict[str, Feature]:
        return self._features

    def __init__(self, **kwargs):
        self._features: dict[str, Feature] = {}
        for _, func in inspect.getmembers(self, lambda x: callable(x) and hasattr(x, MODSTACK_FEATURE)):
            self.add_feature(Feature(func))

    def get_feature[Out, **P](self, name: str, output_type: Type[Out] = Any) -> Feature[Out, P]:
        if name not in self.features:
            raise FeatureNotFound(f'Feature {name} not found in Module {self.__class__.__name__}')
        return self.features[name]

    def add_feature[Out, **P](self, feature: Feature[Out, P]) -> None:
        self.features[feature.name] = feature

    def get_parameters(self, name: str) -> MappingProxyType[str, Parameter]:
        return self.get_feature(name).parameters

    def get_return_annotation(self, name: str) -> Any:
        return self.get_feature(name).return_annotation

    def get_input_schema(self, name: str) -> Type[BaseModel]:
        return self.get_feature(name).input_schema

    def set_input_schema(self, name: str, input_schema: Type[BaseModel]) -> None:
        feature = self.get_feature(name)
        setattr(feature, 'input_schema', input_schema)

    def get_output_schema(self, name: str) -> Type[BaseModel]:
        return self.get_feature(name).output_schema

    def set_output_schema(self, name: str, output_schema: Type[BaseModel]) -> None:
        feature = self.get_feature(name)
        setattr(feature, 'output_schema', output_schema)