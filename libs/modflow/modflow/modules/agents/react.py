from typing import NotRequired, Optional, Sequence, TypedDict, Union

from modflow.checkpoints import Checkpointer
from modflow.managed import ManagedValue
from modflow.modules import StateFlow
from modstack.artifacts.messages import AiMessage, MessageArtifact, SystemMessage
from modstack.modules import Module, ModuleLike, SerializableModule
from modstack.modules.ai import LLMRequest
from modstack.typing import Effect, Effects

_MessageModifier = Union[
    str,
    SystemMessage,
    ModuleLike[list[MessageArtifact], list[MessageArtifact]]
]

class ReactAgentState(TypedDict):
    messages: list[MessageArtifact]
    is_last_step: NotRequired[ManagedValue[bool]]

def create_react_agent(
    model: Module[LLMRequest, MessageArtifact],
    tools: list[ModuleLike],
    message_modifier: Optional[_MessageModifier] = None,
    checkpointer: Optional[Checkpointer] = None,
    interrupt_before: Optional[Sequence[str]] = None,
    interrupt_after: Optional[Sequence[str]] = None,
    debug: bool = False
) -> SerializableModule[ReactAgentState, ReactAgentState]:
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
        llm = (lambda messages: [system_message] + messages) | model
    elif isinstance(message_modifier, SystemMessage):
        llm = (lambda messages: [message_modifier] + messages) | model
    else:
        llm = message_modifier | model

    # Define the function that calls the model
    def call_model(state: ReactAgentState, **kwargs) -> Effect[ReactAgentState]:
        def invoke() -> ReactAgentState:
            response = llm.invoke(
                LLMRequest(
                    prompt=state['messages'][-1],
                    messages=state['messages'][1:] or []
                ),
                **kwargs
            )
            return handle_response(response)

        async def ainvoke() -> ReactAgentState:
            response = await llm.ainvoke(
                LLMRequest(
                    prompt=state['messages'][-1],
                    messages=state['messages'][1:] or []
                ),
                **kwargs
            )
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