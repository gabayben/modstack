import inspect
from inspect import Parameter
from types import MappingProxyType
from typing import Any, TYPE_CHECKING, Type, final

from pydantic import BaseModel

from modstack.constants import MODSTACK_ENDPOINT
from modstack.endpoints import Endpoint, EndpointNotFound

if TYPE_CHECKING:
    from modstack.engines.engine import EngineContext
else:
    EngineContext = Any

class ModuleError(Exception):
    pass

class Module:
    context: EngineContext

    @property
    def endpoints(self) -> dict[str, Endpoint]:
        return self._endpoints

    def __init__(self, **kwargs):
        self._endpoints: dict[str, Endpoint] = {}
        for _, func in inspect.getmembers(self, lambda x: callable(x) and hasattr(x, MODSTACK_ENDPOINT)):
            self.add_endpoint(Endpoint(func))

    def __engine_init__(self) -> None:
        pass

    @final
    def add_context(self, context: EngineContext) -> None:
        self.context = context
        self.__engine_init__()

    @final
    def has_context(self) -> bool:
        return hasattr(self, 'context')

    @final
    def validate_context(self) -> None:
        if not self.has_context():
            raise ModuleError(f'Context is not set. You must add {self.__class__.__name__} to an Engine.')

    def get_endpoint[Out](self, name: str, output_type: Type[Out] = Any) -> Endpoint[Out]:
        if name not in self.endpoints:
            raise EndpointNotFound(f'Endpoint {name} not found in Module {self.__class__.__name__}')
        return self.endpoints[name]

    def add_endpoint[Out](self, endpoint: Endpoint[Out]) -> None:
        self.endpoints[endpoint.name] = endpoint

    def get_parameters(self, endpoint_name: str) -> MappingProxyType[str, Parameter]:
        return self.get_endpoint(endpoint_name).parameters

    def get_return_annotation(self, endpoint_name: str) -> Any:
        return self.get_endpoint(endpoint_name).return_annotation

    def get_input_schema(self, endpoint_name: str) -> Type[BaseModel]:
        return self.get_endpoint(endpoint_name).input_schema

    def set_input_schema(self, endpoint_name: str, input_schema: Type[BaseModel]) -> None:
        endpoint = self.get_endpoint(endpoint_name)
        setattr(endpoint, 'input_schema', input_schema)

    def get_output_schema(self, endpoint_name: str) -> Type[BaseModel]:
        return self.get_endpoint(endpoint_name).output_schema

    def set_output_schema(self, endpoint_name: str, output_schema: Type[BaseModel]) -> None:
        endpoint = self.get_endpoint(endpoint_name)
        setattr(endpoint, 'output_schema', output_schema)