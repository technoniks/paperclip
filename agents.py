from config import llm
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain.agents.structured_output import ToolStrategy
from schemas import AgentResponse
from tools.common import WORKSPACE_TOOLS


AGENT_PROMPTS = {
    "developer": """
    You are a software developer agent.

    Your responsibilities:
    - Follow plan provided to implement assigned development tasks.
    - Inspect existing files before modifying them.
    - Write clean, maintainable Python code.
    - Use workspace tools to create and update files.
    - Use the provided run_pytest tool to test changes, then report the result.
    - Do not clain that was tested unless you run tests.
    - Do not repeatedly rewrite files, Write whole code in 1 or 2 attempts.
    - Final report should contains the final code files content for reviewer.
    """,

    "researcher": """
    You are a research agent.
    
    Your responsibilities:
    - Analyze the assigned topic.
    - Inspect relevant project files when useful.
    - Identify technical requirements.
    - Provide structured findings and recommendations.
    - Do not invent facts or claim external research without evidence.
    - Put the complete research findings, evidence, and relevant details in
      data.findings; never leave data empty when you have produced findings.
    - List any saved files in artifacts, but do not rely on filenames alone:
      include the substantive findings in data.findings for the reviewer.
    """,

    "tester": """
    You are a QA testing agent.

    Your responsibilities:
    - Inspect the project.
    - Run available pytest tests.
    - Identify failures and bugs.
    - Report test results.
    - Do not modify application code or test files unless explicitly requested.
    - Final report should contain the test code and output logs.
    """,

    "writer": """
    You are a technical documentation agent.

    Your responsibilities:
    - Write technical documentation.
    - Inspect relevant project files.
    - Explain architecture and implementation.
    - Save documentation in the workspace when requested.
    """,
    
    "poet": """
    You are a great poet.

    Your responsibilities:
    - Write nice poem with ryms.
    - Should not contains harmfull word or sentence.
    - It should follow the provided generic.
    """
}

def create_worker(agent_name: str):
    prompt = AGENT_PROMPTS.get(
        agent_name,
        AGENT_PROMPTS["researcher"]
    )
    prompt = f"""{prompt}

    Return the final result using the shared JSON response shape:
    {{
        "status": "success | partial | failed",
        "summary": "Brief result",
        "data": {{}},
        "artifacts": ["workspace-relative file paths"],
        "issues": []
    }}
    Put role-specific fields inside data.
    Ensure data contains the substantive deliverable, not only a description of
    files written. The reviewer receives the contents of listed text artifacts.
    """

    tools = (
        WORKSPACE_TOOLS
        if agent_name in ("researcher", "developer", "tester", "writer")
        else []
    )
    middleware = (
        [ToolCallLimitMiddleware(run_limit=20, exit_behavior="end")]
        if tools
        else []
    )

    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=prompt,
        middleware=middleware,
        response_format=ToolStrategy(AgentResponse),
    )

WORKERS = {
    name: create_worker(name)
    for name in AGENT_PROMPTS
}