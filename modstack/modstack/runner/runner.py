from collections import defaultdict
from typing import AsyncIterator, Iterator, final

from modstack.containers import AmbiguousFeatures, Effect, Feature, FeatureNotFound

from modstack.contracts import Contract
from modstack.modules import Module
from modstack.typing.vars import Out

@final
class Runner:
    @property
    def features(self) -> dict[str, dict[str, Feature]]:
        return self._features

    @property
    def modules(self) -> list[Module]:
        return self._modules

    def __init__(self):
        self._features: dict[str, dict[str, Feature]] = defaultdict(dict)
        self._modules: list[Module] = []

    def add_feature(self, feature: Feature, provider: str | None = None) -> None:
        provider = provider or feature.name
        self.features[feature.name][provider] = feature

    def add_module(self, module: Module, name: str | None = None):
        name = name or module.__class__.__name__
        for feature in module.endpoints.values():
            self.add_feature(feature, provider=name)

    def get_feature(self, contact: Contract[Out], provider: str | None = None) -> Feature[Out]:
        features = self.features[contact.name()]
        if len(features) == 0:
            raise FeatureNotFound(f"Feature '{contact.name()}' not registered.")
        if len(features) == 1:
            return list(features.values())[0] #type: ignore
        if provider is None:
            raise AmbiguousFeatures(f"Multiple features for '{contact.name()} were found. You must specify a provider.")
        try:
            return features[provider] #type: ignore
        except KeyError as e:
            raise FeatureNotFound(f"Feature '{contact.name()}' not found for provider '{provider}'.") from e

    def effect(self, contract: Contract[Out], provider: str | None = None) -> Effect[Out]:
        return self.get_feature(contract, provider=provider)(**dict(contract))

    def invoke(self, contract: Contract[Out], provider: str | None = None) -> Out:
        return self.effect(contract, provider=provider).invoke()

    async def ainvoke(self, contract: Contract[Out], provider: str | None = None) -> Out:
        return await self.effect(contract, provider=provider).ainvoke()

    def iter(self, contract: Contract[Out], provider: str | None = None) -> Iterator[Out]:
        yield from self.effect(contract, provider=provider).iter()

    async def aiter(self, contract: Contract[Out], provider: str | None = None) -> AsyncIterator[Out]:
        async for item in self.effect(contract, provider=provider).aiter(): #type: ignore
            yield item