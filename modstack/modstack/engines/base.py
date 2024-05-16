from abc import ABC, abstractmethod

from modstack.modules import Module

class EngineBase(ABC):
    @abstractmethod
    def to_module(self) -> Module:
        pass