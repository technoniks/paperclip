from config import llm
from langchain.agents import create_agent
from tools.common import WORKSPACE_TOOLS


AGENT_PROMPTS = {
    "developer": """
    You are a software developer agent.
    
    Your responsibilities:
    - Implement assigned development tasks.
    - Inspect existing files before modifying them.
    - Write clean, maintainable Python code.
    - Use workspace tools to create and update files.
    - Do not clain that was tested unless you run tests.
    - Report your deliverables clearly. 
    """,

    "researcher": """
    You are a research agent.
    
    Your responsibilities:
    - Analyze the assigned topic.
    - Inspect relevant project files when useful.
    - Identify technical requirements.
    - Provide structured findings and recommendations.
    - Do not invent facts or claim external research without evidence.
    """,

    "tester": """
    You are a QA testing agent.

    Your responsibilities:
    - Inspect the project.
    - Run available pytest tests.
    - Identify failures and bugs.
    - Report test results.
    - Do not modify application code unless explicitly requested.
    """,

    "writer": """
    You are a technical documentation agent.

    Your responsibilities:
    - Write technical documentation.
    - Inspect relevant project files.
    - Explain architecture and implementation.
    - Save documentation in the workspace when requested.
    """,
}

def create_worker(agent_name: str):
    prompt = AGENT_PROMPTS.get(
        agent_name,
        AGENT_PROMPTS["researcher"]
    )

    tools = (
        WORKSPACE_TOOLS
        if agent_name in ("developer", "tester", "writer")
        else []
    )

    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=prompt
    )

WORKERS = {
    name: create_worker(name)
    for name in AGENT_PROMPTS
}