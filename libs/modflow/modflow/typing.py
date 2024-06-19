from collections import deque
from typing import Any, Literal, NamedTuple, NotRequired, Optional, Sequence, TypedDict, Union

from modflow.checkpoints import CheckpointMetadata
from modstack.modules import Module

FlowInput = Union[dict[str, Any], Any]
FlowOutputChunk = Union[dict[str, Any], Any]
FlowOutput = Union[FlowOutputChunk, list[FlowOutputChunk]]
All = Literal['*']
StreamMode = Literal['values', 'updates', 'debug']

class FlowOptions(TypedDict, total=False):
    input_keys: NotRequired[Union[str, Sequence[str]]]
    output_keys: NotRequired[Union[str, Sequence[str]]]
    interrupt_before: NotRequired[Union[Sequence[str], All]]
    interrupt_after: NotRequired[Union[Sequence[str], All]]
    config: NotRequired[dict[str, Any]]
    stream_mode: NotRequired[StreamMode]
    debug: NotRequired[bool]
    recursion_limit: NotRequired[int]

class PregelTaskDescription(NamedTuple):
    name: str
    data: Any

class PregelExecutableTask(NamedTuple):
    name: str
    data: Any
    process: Module
    writes: deque[tuple[str, Any]]
    triggers: list[str]
    kwargs: dict[str, Any]

class StateSnapshot(NamedTuple):
    values: FlowOutputChunk
    next: tuple[str, ...]
    created_at: Optional[str]
    metadata: Optional[CheckpointMetadata]
    kwargs: dict[str, Any]

class Send:
    """
    A message or packet to send to a specific node in the flow.

    The `Send` class is used within a `StateFlow`'s conditional edges to dynamically
    route states to different nodes based on certain conditions. This enables
    creating "map-reduce" like flows, where a node can be invoked multiple times
    in parallel on different states, and the results can be aggregated back into the
    main flow's state.

    Attributes:
        node (str): The name of the target node to send the message to.
        arg (Any): The state or message to send to the target node.

    Examples:
        class OverallState(TypedDict):
            subjects: list[str]
            jokes: Annotated[list[str], operator.add]

        def continue_to_jokes(state: OverallState):
            return [Send("generate_joke", {"subject": s}) for s in state['subjects']]

        builder = StateFlow(OverallState)
        builder.add_node("generate_joke", lambda state: {"jokes": [f"Joke about {state['subject']}"]})
        builder.add_conditional_edges(START, continue_to_jokes)
        builder.add_edge("generate_joke", END)
        flow = builder.compile()
        flow.invoke({"subjects": ["cats", "dogs"]})
        {'subjects': ['cats', 'dogs'], 'jokes': ['Joke about cats', 'Joke about dogs']}
    """

    node: str
    arg: Any

    def __init__(self, node: str, arg: Any):
        self.node = node
        self.arg = arg

    def __hash__(self) -> int:
        return hash((self.node, self.arg))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Send)
            and self.node == other.node
            and self.arg == other.arg
        )

    def __repr__(self) -> str:
        return f'Send(node={self.node!r}, arg={self.arg!r})'