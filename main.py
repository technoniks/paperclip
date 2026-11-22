import time
import uuid

from state import ExecutionState
from graph.workflow import build_workflow


def main():

    graph = build_workflow()

    initial_state: ExecutionState = {
        "goal": (
            "Create a Python calculator application "
            "with addition, subtraction, multiplication, "
            "division and unit tests."
        ),

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

    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        },
        "recursion_limit": 100,
    }

    print("\nStarting AI organization...\n")

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