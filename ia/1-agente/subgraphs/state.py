import logging
from typing import Literal, Optional

from langgraph.graph import START, StateGraph
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage, AnyMessage

class AssistantState(TypedDict):
    """State of the assistant."""

    messages: Annotated[list[AnyMessage], add_messages]
    token: str = None
    # config: str = None
    document: str = None
    isAnnonymous: bool = True
    user_name: str = None
    language: str = None

    # JML: Do not use Literal, it will be dropped by the graph
    # intent = Literal[ "survey_agent", "chat_agent", "none" ]
