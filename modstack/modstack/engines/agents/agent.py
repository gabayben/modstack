from modstack.engines import EngineBase
from modstack.modules import Module

class Agent(EngineBase):
    def to_module(self) -> Module:
        pass