
from langgraph.types import StateSnapshot
from subgraphs.state import AssistantState

def innermost_subgraph_state(state: AssistantState, depth: int = 0) -> StateSnapshot:
    # print(type(state))
    if state is None:
        # print(f'depth={depth} None')
        raise ValueError("State is None")
    # print(f'depth={depth}, len={len(state.tasks)}')
    # print_messages(state.values['messages'])
    if len(state.tasks) == 0 or state.tasks[0].state is None:
        # print(f'depth={depth}, len={len(state.tasks)} returning messages={len(state.values['messages'])}')
        return state
    return innermost_subgraph_state(state.tasks[0].state, depth + 1)