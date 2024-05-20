from typing import ParamSpec, TypeVar, TypeVarTuple

Args = TypeVarTuple('Args')
P = ParamSpec('P')
In = TypeVar('In', bound=dict)
Out = TypeVar('Out')
Other = TypeVar('Other')