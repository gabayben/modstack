from typing import ParamSpec, TypeVar, TypeVarTuple

from pydantic import BaseModel

Args = TypeVarTuple('Args')
P = ParamSpec('P')
In = TypeVar('In', bound=BaseModel)
Out = TypeVar('Out')
Other = TypeVar('Other')