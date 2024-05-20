from typing import Any, TYPE_CHECKING, Type

from modstack.endpoints import Endpoint
from modstack.engines import EngineEndpointError, EngineModuleError
from modstack.engines.base import EngineBase
from modstack.typing.vars import Out

if TYPE_CHECKING:
    from modstack.modules.base import Module
else:
    Module = Any

class Engine(EngineBase):
    @property
    def modules(self) -> dict[str, Module]:
        return self._modules

    @property
    def endpoints(self) -> dict[str, Endpoint]:
        return self._endpoints

    def __init__(self, name: str | None = None):
        self.name = name or self.__class__.__name__
        self._modules: dict[str, Module] = {}
        self._endpoints: dict[str, Endpoint] = {}

    def as_context(self) -> 'EngineContext':
        return EngineContext(self)

    def add_module[TModule: Module](
        self,
        name: str,
        module: TModule,
        include: list[str] | None = None,
        flatten_single: bool = True
    ) -> TModule:
        if name in self.modules:
            raise EngineModuleError(f"Module '{name}' already exists in engine.")
        self.modules[name] = module

        endpoints: list[Endpoint] = list(module.endpoints.values())
        if include:
            endpoints = [endpoint for endpoint in endpoints if endpoint.name in include]

        if flatten_single and len(endpoints) == 1:
            try:
                self.add_endpoint(endpoints[0], path=name)
            except EngineEndpointError as e:
                raise EngineEndpointError(
                    f"Endpoint '{name}' already exists in engine. Set `flatten_single` to False "
                    f"in order to include both the module and endpoint names in the path."
                ) from e
        else:
            for endpoint in endpoints:
                self.add_endpoint(endpoint, path=f'{name}.{endpoint.name}')

        return module

    def add_endpoint(self, endpoint: Endpoint, path: str | None = None) -> None:
        path = path or endpoint.name
        if path in self.endpoints:
            raise EngineEndpointError(f"Endpoint '{path}' already exists in engine.")
        self.endpoints[path] = endpoint

    def get_endpoint(
        self,
        path: str,
        output_type: Type[Out] = Any
    ) -> Endpoint[Out]:
        if path not in self.endpoints:
            raise EngineEndpointError(f"Endpoint '{path}' not found in engine.")
        return self.endpoints[path]

class EngineContext(EngineBase):
    def __init__(self, engine: Engine):
        self._engine = engine

    def get_endpoint(
        self,
        path: str,
        output_type: Type[Out] = Any
    ) -> Endpoint[Out]:
        return self._engine.get_endpoint(path, output_type=output_type)