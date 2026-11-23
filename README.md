# Paperclip

Paperclip is a small Python prototype for coordinating AI agents around a goal.
It uses LangGraph to manage the workflow, LangChain agents to perform tasks,
and Google Gemini models for planning, worker execution, review, and reporting.

The project is designed to let a manager divide a goal into tasks, route each
task to a specialist worker, review the result, and produce a final report.
Workers can use a small set of tools to work in an isolated output directory.

## How it works

The workflow in `graph/workflow.py` runs these stages:

1. **Manager** asks the JSON-configured model to create a plan of one to five
   tasks and assign each task to an agent.
2. **Dispatcher** selects the next pending task, subject to the execution
   limits.
3. **Worker** invokes the assigned agent. The configured agents are developer,
   researcher, tester, writer, and poet. The first four have workspace tools;
   the poet currently has no tools.
4. **Reviewer** evaluates the worker result and any available artifact
   contents, then approves or rejects the task.
5. **Finalizer** summarizes completed, failed, and pending work.

The worker response follows the shared `AgentResponse` shape:

```json
{
  "status": "success",
  "summary": "Brief result",
  "data": {},
  "artifacts": [],
  "issues": []
}
```

Role-specific details belong in `data`. Workspace-relative output paths belong
in `artifacts`. The workflow reads listed artifact files and includes their
text in the reviewer handoff where possible.

## Requirements

- Python 3.10 or later
- A Google Gemini API key
- Network access to the Google Gemini API

Dependencies are listed in `requirements.txt`. The configured model names and
reasoning levels are in `config.py`; the worker and JSON clients are configured
separately.

## Setup

From the project root, create and activate a virtual environment, then install
the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Create a `.env` file in the project root and add your Google API key:

```dotenv
GOOGLE_API_KEY=your-google-api-key
```

`config.py` loads `.env` using `python-dotenv`. The `.env` file is ignored by
Git; do not commit API keys.

## Run

With the virtual environment active:

```bash
python main.py
```

When the program starts, it prompts for a goal. Enter the goal and press
Return; the input is trimmed, and an empty goal is rejected before the
workflow or workspace is started. Each accepted goal is passed into the
manager and used for that run.

Example goals:

1. Write a recipe for tea.
2. Write a 12-line romantic poem that follows a rhyme scheme.
3. Create a simple RAG implementation using Qdrant running locally (installed
   locally, not in Docker), the already-pulled Ollama `qwen3.5:2b` model with
   reasoning off, and `nomic-embed-text:latest` for embeddings.

At startup the application creates a numbered workspace directory under
`workspace/` (for example, `workspace/001`) and prints its path. New runs use
the next available number. Generated workspace contents are ignored by Git.

## Workspace tools

The tools are defined in `tools/common.py` and operate within the active
numbered workspace:

- `list_files` lists files in the active workspace.
- `read_file` reads a text file by workspace-relative path.
- `write_file` creates or replaces a text file by workspace-relative path.
- `run_pytest` runs `python -m pytest -q` in the active workspace, using the
  same Python interpreter as the application. The test command has a
  30-second timeout.

Paths are resolved and checked to prevent accessing files outside the active
workspace. Tool-enabled worker runs are limited to 20 tool calls.

## Project layout

```text
.
├── agents.py             # Specialist agent prompts and construction
├── config.py             # Gemini model configuration and .env loading
├── main.py               # Initial execution state and application entry point
├── schemas.py            # Shared structured worker response
├── state.py              # LangGraph state and task types
├── graph/
│   ├── nodes.py           # Manager, dispatcher, worker, reviewer, finalizer
│   └── workflow.py        # LangGraph node and edge definitions
├── tools/
│   └── common.py          # Workspace isolation and agent tools
├── workspace/             # Numbered run outputs; ignored by Git
└── requirements.txt       # Python dependencies
```

## Execution limits and current limitations

The initial state in `main.py` sets an eight-step worker execution limit, up to
two attempts per task, and a 300-second time budget. These values can be
adjusted there. The graph also has a LangGraph recursion limit of 100.

This is a prototype, not a fully general autonomous organization:

- The researcher has workspace tools but no dedicated web-search or browser
  tool. Do not treat it as having performed live external research unless an
  external research capability is explicitly added and used.
- The final report and manager/reviewer responses are generated by model
  prompts; review is not a substitute for human verification.
- The active goal and model settings are currently code-configured.

## Troubleshooting

- **Authentication errors:** confirm `.env` is in the project root and contains
  a valid `GOOGLE_API_KEY`.
- **Model not found or unavailable:** check whether the configured model in
  `config.py` is available to your Google API project.
- **`No module named pytest`:** activate the same virtual environment used to
  run the app, then install dependencies with `python -m pip install -r
  requirements.txt`.
- **Unexpected or incomplete worker output:** inspect the run's numbered
  directory under `workspace/`, the printed worker/reviewer messages, and the
  corresponding prompts in `agents.py` and `graph/nodes.py`.
