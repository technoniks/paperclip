import time
import uuid

from state import ExecutionState
from graph.workflow import build_workflow
from tools.common import set_goal_workspace


def main():
    goal = input("Enter your goal: ").strip()
    if not goal:
        raise ValueError("Goal cannot be empty")

    initial_state: ExecutionState = {
        "goal": goal,
        # "create simple rag implementation plan using qdrant running locally "
        # "(local dqrant installation, not docker),"
        # "ollama qwen3.5:2b(reasoning off) model which is already pulled in local, just connect with it"
        # "and nomic-embed-text:latest for embedding.",

        "tasks": [],
        "current_task": None,

        "results": [],
        "events": [],

        "max_steps": 8,
        "steps_used": 0,
        "max_retries": 2,
        "time_budget_seconds": 300,
        "started_at": time.monotonic(),

        "status": "starting",
        "final_answer": "",
    }

    goal_workspace = set_goal_workspace(initial_state["goal"])
    graph = build_workflow()

    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        },
        "recursion_limit": 100,
    }

    print(f"\nStarting AI organization in {goal_workspace}...\n")

    for event in graph.stream(
        initial_state,
        config=config,
        stream_mode="updates",
    ):
        for node_name, output in event.items():
            print(f"\n[{node_name.upper()}]")

            if "events" in output:
                latest = output["events"][-1]
                print(latest["message"])

            if node_name == "finalizer":
                print(output["final_answer"])

    print("\nExecution finished.")


if __name__ == "__main__":
    main()