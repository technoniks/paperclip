import subprocess
import sys

from pathlib import Path
from langchain_core.tools import tool

WORKSPACE_ROOT = Path("workspace").resolve()
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
WORKSPACE = WORKSPACE_ROOT

debug = True  # Set to True to enable debug prints for tool calls

def set_goal_workspace(goal: str) -> Path:
    global WORKSPACE

    if not goal.strip():
        raise ValueError("Goal must not be empty")

    existing_numbers = (
        int(path.name)
        for path in WORKSPACE_ROOT.iterdir()
        if path.is_dir() and path.name.isascii() and path.name.isdecimal()
    )
    next_number = max(existing_numbers, default=0) + 1

    while True:
        candidate = WORKSPACE_ROOT / f"{next_number:03d}"
        try:
            candidate.mkdir()
        except FileExistsError:
            next_number += 1
            continue

        WORKSPACE = candidate.resolve()
        return WORKSPACE

def safe_path(path: str) -> Path:
    target = (WORKSPACE / path).resolve()
    
    if not target.is_relative_to(WORKSPACE):
        raise ValueError("Path outside workspace is not allowed")
    
    return target

@tool
def list_files() -> str:
    """List files in the agent workspace."""
    if debug:
        print("list_files called")
    files = [
        str(p.relative_to(WORKSPACE))
        for p in WORKSPACE.rglob("*")
        if p.is_file()
    ]
    return "\n".join(files) or "Workspace is empty"

@tool
def read_file(path: str) -> Path:
    """Read a text file from the workspace."""
    if debug:
        print(f"read_file called with path: {path}")
    target = safe_path(path)

    if not target.is_file():
        return "File not found"
    
    return target.read_text(encoding="utf-8")

@tool
def write_file(path: str, content: str) -> str:
    """Create or update a text file in the workspace."""
    if debug:
        print(f"write_file called with path: {path}")
    target = safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    return f"Successfully wrote: {path}"

@tool
def run_pytest() -> str:
    """Run pytest against the workspace."""
    if debug:
        print("run_pytest called")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )
        if debug:
            print(f"run_pytest: {result.stdout}")
        return (
            f"Exit code: {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
    except subprocess.TimeoutExpired:
        return "Tests exceeded the 30-seconds timeout"

WORKSPACE_TOOLS = [
    list_files,
    read_file,
    write_file,
    run_pytest,
]
