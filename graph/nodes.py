import json, time, uuid
from langchain.agents import create_agent
from config import json_llm
from state import ExecutionState, AgentEvent, Task
from agents import WORKERS
from tools.common import safe_path

def call_json(prompt: str) -> dict:
    start = time.monotonic()
    response = json_llm.invoke(prompt)
    end = time.monotonic()
    print(f"[DEBUG] JSON call took {end - start:.2f} seconds")
    try:
        return json.loads(response.content[0]['text'])
    except (json.JSONDecodeError, TypeError):
        raise ValueError(
            f"Model did not return valid JSON: {response.content}"
        )

def add_event(state: ExecutionState, agent, action, message) -> list[AgentEvent]:
    return state["events"] + [{
        "step": state["steps_used"],
        "agent": agent,
        "action": action,
        "message": message
    }]

def budget_exhausted(state: ExecutionState):
    elapsed = time.monotonic() - state["started_at"]

    return (
        state["steps_used"] >= state["max_steps"]
        or elapsed >= state["time_budget_seconds"]
    )

def manager_node(state: ExecutionState):
    prompt = f"""
    You are the CEO and project manager of an AI organization.

    User Goal:
    {state["goal"]}

    Break the goal into small executable tasks.

    Available agents:
    - developer
    - researcher
    - tester
    - writer

    Rules:
    1. Create between 1 to 5 tasks.
    2. Assign one agent to each tasks.
    3. Tasks must have clear deliverables.
    4. Include task dependencies inn description where necessary.
    5. Do not assign a tester before implementation when testing depends on code.

    Return ONLY valid JSON:

    {{
        "tasks": [{{
            "title": "Task Title",
            "description": "Detailed instruction",
            "agent": "developer",
        }}]
    }} 
    """
    data = call_json(prompt)
    tasks = []
    for item in data.get("tasks", []):
        agent = item.get("agent", "researcher")

        if agent not in WORKERS:
            agent = "researcher"

        tasks.append({
            "id": str(uuid.uuid4())[:8],
            "title": item["title"],
            "description": item["description"],
            "agent": agent,
            "status": "pending",
            "attempts": 0,
            "result": "",
            "review": "",
        })

    if not tasks:
        raise ValueError("Manager created an empty task plan")
    return {
        "tasks": tasks,
        "status": "running",
        "events": add_event(
            state,
            "manager",
            "plan",
            f"Created {len(tasks)} tasks: {', '.join([t['title'] + ': ' + t['agent']  for t in tasks])}",
        ),
    }

def dispatcher_node(state: ExecutionState):
    if budget_exhausted(state):
        return {
            "current_task": None,
            "status": "limit_reached",
        }

    for task in state["tasks"]:
        if task["status"] == "pending":
            return {
                "current_task": task,
                "events": add_event(
                    state,
                    "manager",
                    "assign",
                    f"Assigned {task['title']} to {task['agent']}",
                ),
            }
    return {
        "current_task": None,
    }

def worker_node(state: ExecutionState):
    task = state["current_task"]
    worker = WORKERS[task["agent"]]

    prompt = f"""
    PROJECT GOAL: {state['goal']}

    YOUR ASSIGNED TASK: {task['title']}

    TASK DETAILS: {task['description']}

    PREVIOUS COMPLETED RESULTS: {json.dumps(state['results'], ensure_ascii=False)}

    Execute your assigned task.

    Use your tools when required.

    Return the shared JSON response with the substantive result in data. For
    research tasks, include the complete findings in data.findings, not only a
    summary or saved-file path. List workspace-relative output paths in
    artifacts; their text contents will also be attached for the reviewer.
    """

    task["status"] = "running"
    task["attempts"] += 1

    try:
        start = time.monotonic()
        response = worker.invoke({
            "messages": [{"role": "user", "content": prompt}]
        })
        end = time.monotonic()
        print(f"[DEBUG] Worker {task['agent']} call took {end - start:.2f} seconds")
        worker_result = response["structured_response"]
        result_data = worker_result.model_dump()
        artifact_contents = {}

        for artifact in worker_result.artifacts:
            try:
                artifact_path = safe_path(artifact)
                if not artifact_path.is_file():
                    worker_result.issues.append(
                        f"Artifact does not exist or is not a file: {artifact}"
                    )
                    continue
                artifact_contents[artifact] = artifact_path.read_text(
                    encoding="utf-8"
                )
            except (OSError, UnicodeError, ValueError) as exc:
                worker_result.issues.append(
                    f"Could not read artifact {artifact}: {exc}"
                )

        if artifact_contents:
            result_data["data"]["artifact_contents"] = artifact_contents
        result_data["issues"] = worker_result.issues
        result = json.dumps(result_data, ensure_ascii=False)
    except Exception as e:
        result = f"Worker execution failed: {e}"

    return {
        "current_task": {
            **task,
            "result": result,
        },
        "steps_used": state["steps_used"] + 1,
        "events": add_event(
            state,
            task["agent"],
            "execute",
            f"Executed task: {task['title']}",
        )
    }

def reviewer_node(state: ExecutionState):

    task: Task = state["current_task"]
    prompt = f"""
    You are an independent QA reviewer.

    PROJECT GOAL: {state["goal"]}

    TASK: {task["title"]}

    REQUIREMENTS: {task["description"]}

    WORKER RESULT: {task["result"]}

    Review the result.
    The worker result includes its structured data and, when available, the
    full text of every listed artifact under data.artifact_contents. Review
    that content rather than approving based on filenames or summaries alone.
    Do not approve if the substantive deliverable is absent from data, or if a
    listed artifact is missing from artifact_contents and its content is not
    otherwise included in data.

    Approve only if the deliverable meets the task requirements.
    If the task requires testing, distinguish actual test evidence
    from a worker's unverified claim.

    Return ONLY valid JSON:

    {{
        "approved": true,
        "feedback": "Review explanation"
    }}
    """

    try:
        review = call_json(prompt)

        approved = review.get("approved") is True
        feedback = str(review.get("feedback", ""))

    except Exception as exc:
        approved = False
        feedback = f"Review failed: {exc}"

    task["review"] = feedback

    if approved:
        task["status"] = "completed"

    elif task["attempts"] < state["max_retries"]:
        task["status"] = "pending"

    else:
        task["status"] = "failed"

    updated_tasks = [
        task if t["id"] == task["id"] else t
        for t in state["tasks"]
    ]

    results = state["results"] + [{
        "task_id": task["id"],
        "title": task["title"],
        "agent": task["agent"],
        "result": task["result"],
        "approved": approved,
        "feedback": feedback,
    }]

    return {
        "tasks": updated_tasks,
        "current_task": task,
        "results": results,
        "events": add_event(
            state,
            "reviewer",
            "approve" if approved else "reject",
            feedback,
        ),
    }

def finalizer_node(state: ExecutionState):

    completed = [
        t for t in state["tasks"]
        if t["status"] == "completed"
    ]

    failed = [
        t for t in state["tasks"]
        if t["status"] == "failed"
    ]

    pending = [
        t for t in state["tasks"]
        if t["status"] == "pending"
    ]

    if failed or pending:
        status = "partial"
    elif len(completed) == len(state["tasks"]):
        status = "completed"
    else:
        status = "partial"

    prompt = f"""
    You are the CEO of an AI organization.

    ORIGINAL GOAL: {state["goal"]}

    EXECUTION RESULTS: {json.dumps(state["results"], ensure_ascii=False)}

    TASK STATUS:
    Completed: {len(completed)}
    Failed: {len(failed)}
    Pending: {len(pending)}

    EXECUTION STATUS: {status}

    Prepare a final report.

    Include:
    1. Summary of work.
    2. Completed tasks.
    3. Failed or pending tasks.
    4. Important limitations.
    5. Recommended next steps.
    """

    start = time.monotonic()
    response = json_llm.invoke(prompt)
    end = time.monotonic()

    print(f"[DEBUG] Finalizer call took {end - start:.2f} seconds")

    return {
        "status": status,
        "final_answer": response.content[-1]["text"],
        "current_task": None,
    }

    