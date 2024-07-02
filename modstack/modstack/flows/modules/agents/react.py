from typing import NotRequired, Optional, Sequence, TypedDict, Union

from modstack.flows.checkpoints import Checkpointer
from modstack.flows.constants import END
from modstack.flows.managed import ManagedValue
from modstack.flows.modules import StateFlow
from modstack.artifacts.messages import AiMessage, MessageArtifact, SystemMessage
from modstack.core import ModuleLike, SerializableModule, coerce_to_module
from modstack.ai import LLM, LLMPrompt
from modstack.ai.tools import ToolExecutor
from modstack.typing import Effect, Effects

_MessageModifier = Union[
    str,
    SystemMessage,
    ModuleLike[LLMPrompt, LLMPrompt]
]

class ReactAgentState(TypedDict):
    messages: list[MessageArtifact]
    is_last_step: NotRequired[ManagedValue[bool]]

def create_react_agent(
    model: LLM,
    tools: list[ModuleLike],
    message_modifier: Optional[_MessageModifier] = None,
    checkpointer: Optional[Checkpointer] = None,
    interrupt_before: Optional[Sequence[str]] = None,
    interrupt_after: Optional[Sequence[str]] = None,
    debug: bool = False
) -> SerializableModule[ReactAgentState, ReactAgentState]:
    tools = [coerce_to_module(tool) for tool in tools]

    # Define the function that determines whether to continue or not
    def should_continue(state: ReactAgentState) -> str:
        last_message = state['messages'][-1]
        if not isinstance(last_message, AiMessage) or not last_message.tool_calls:
            # If there is no function call, then we finish
            return 'end'
        # Otherwise if there is, we continue
        return 'continue'

    # Add the message modifier, if exists
    if message_modifier is None:
        llm = model
    elif isinstance(message_modifier, str):
        system_message = SystemMessage(message_modifier)
        llm = (lambda prompt: prompt + LLMPrompt([system_message])) | model
    elif isinstance(message_modifier, SystemMessage):
        llm = (lambda prompt: prompt + LLMPrompt([message_modifier])) | model
    else:
        llm = message_modifier | model

    # Define the function that calls llm
    def call_model(state: ReactAgentState, **kwargs) -> Effect[ReactAgentState]:
        def invoke() -> ReactAgentState:
            response = llm.invoke(LLMPrompt(state['messages']), **kwargs)
            return handle_response(response)

        async def ainvoke() -> ReactAgentState:
            response = await llm.ainvoke(LLMPrompt(state['messages']), **kwargs)
            return handle_response(response)

        def handle_response(response: MessageArtifact) -> ReactAgentState:
            if state['is_last_step'] and isinstance(response, AiMessage) and response.tool_calls:
                return {
                    'messages': [AiMessage(
                        content='Sorry, need more steps to process this request.',
                        id=response.id
                    )]
                }

            # We return a list, because this will get added to the existing list
            return {'messages': [response]}

        return Effects.From(invoke=invoke, ainvoke=ainvoke)

    # Define a new flow
    flow = StateFlow(ReactAgentState)

    # Define the two nodes that the agent will cycle between
    flow.add_node(call_model, 'agent')
    flow.add_node(ToolExecutor(tools), 'tools')

    # Set the entrypoint as `agent`, this means that this node is the first one called
    flow.set_entry_point('agent')

    # Conditional edge
    flow.add_conditional_edges(
        'agent',
        should_continue,
        path_map={'continue': 'tools', 'end': END}
    )

    # Add an edge from `tools` to `agent`
    flow.add_edge('tools', 'agent')

    # Compile and return flow
    return flow.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_before,
        interrupt_after=interrupt_after,
        debug=debug
    )