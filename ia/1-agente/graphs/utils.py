from langgraph.types import StateSnapshot

def innermost_subgraph_state(state_snapshot: StateSnapshot, depth: int = 0) -> StateSnapshot:
    """
    Extract the innermost subgraph state from a StateSnapshot.
    
    Args:
        state_snapshot: The StateSnapshot containing the graph state
        depth: Current recursion depth (for debugging)
        
    Returns:
        The innermost state values from the subgraph hierarchy
    """
    if state_snapshot is None:
        raise ValueError("StateSnapshot is None")
    
    # If no tasks or first task has no state, return the current state values
    if len(state_snapshot.tasks) == 0 or state_snapshot.tasks[0].state is None:
        return state_snapshot
    
    # Recursively get the innermost state
    return innermost_subgraph_state(state_snapshot.tasks[0].state, depth + 1)