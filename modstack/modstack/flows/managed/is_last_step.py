"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/managed/is_last_step.py
"""

from typing import Annotated

from modstack.flows import PregelTaskDescription
from modstack.flows.managed import ManagedValue

class IsLastStepValue(ManagedValue[bool]):
    def __call__(self, step: int, task: PregelTaskDescription) -> bool:
        return step == self.kwargs.get('recursion_limit', 0) - 1

IsLastStep = Annotated[bool, IsLastStepValue]