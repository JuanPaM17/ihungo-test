from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage


class AssistantState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    document: str
    is_anonymous: bool
    token: str
    user_name: str
    language: str

class EvaluatorState(AssistantState):
    trial: int
