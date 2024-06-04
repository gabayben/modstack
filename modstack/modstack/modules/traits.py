from abc import ABC, abstractmethod
from typing import Type

from pydantic import BaseModel

class HasSequentialSchema(ABC):
    @abstractmethod
    def seq_input_schema(self, next_schema: Type[BaseModel]) -> Type[BaseModel]:
        pass

    @abstractmethod
    def seq_output_schema(self, prev_schema: Type[BaseModel]) -> Type[BaseModel]:
        pass