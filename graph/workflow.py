from state import ExecutionState
from langgraph.graph import StateGraph, START, END
from graph.nodes import budget_exhausted, manager_node, worker_node, finalizer_node, reviewer_node, dispatcher_node

def route_after_dispatch(state: ExecutionState):

    if state["current_task"] is None:
        return "finalizer"

    return "worker"


def route_after_review(state: ExecutionState):

    if budget_exhausted(state):
        return "dispatcher"

    return "dispatcher"


def build_workflow():

    builder = StateGraph(ExecutionState)

    # Register nodes
    builder.add_node("manager", manager_node)
    builder.add_node("dispatcher", dispatcher_node)
    builder.add_node("worker", worker_node)
    builder.add_node("reviewer", reviewer_node)
    builder.add_node("finalizer", finalizer_node)

    # Execution flow
    builder.add_edge(START, "manager")

    builder.add_edge("manager", "dispatcher")

    builder.add_conditional_edges(
        "dispatcher",
        route_after_dispatch,
        {
            "worker": "worker",
            "finalizer": "finalizer",
        },
    )

    builder.add_edge("worker", "reviewer")

    builder.add_conditional_edges(
        "reviewer",
        route_after_review,
        {
            "dispatcher": "dispatcher",
        },
    )

    builder.add_edge("finalizer", END)

    return builder.compile()