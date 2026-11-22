from typing import TypedDict, Literal, Any

class Task(TypedDict):
    id: int
    title: str
    description: str
    agent: str
    status: Literal[
        "pending", 
        "running", 
        "completed",
        "failed"
    ]
    attempts: int
    result: str
    review: str

class AgentEvent(TypedDict):
    step: str
    agent: str
    action: str
    message: str

class ExecutionState(TypedDict):
    # User request
    goal: str

    # Execution plan
    tasks: list[Task]
    current_task: Task | None

    # Execution history
    results: list[dict[str, Any]]
    events: list[AgentEvent]

    # Execution limits
    max_steps: int
    steps_used: int
    max_retries: int
    time_budget_seconds: int
    started_at: float

    # Final status
    status: str
    final_answer: str