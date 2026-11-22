import subprocess

from pathlib import Path
from langchain_core.tools import tool

WORKSPACE = Path("workspace").resolve()
WORKSPACE.mkdir(exist_ok=True)

def safe_path(path: str) -> Path:
    target = (WORKSPACE / path).resolve()
    
    if not target.is_relative_to(WORKSPACE):
        raise ValueError("Path outside workspace is not allowed")
    
    return target

@tool
def list_files() -> str:
    """List files in the agent workspace."""

    files = [
        str(p.relative_to(WORKSPACE))
        for p in WORKSPACE.rglob("*")
        if p.is_file()
    ]
    return "\n".join(files) or "Workspace is empty"

@tool
def read_file(path: str) -> Path:
    """Read a text file from the workspace."""

    target = safe_path(path)

    if not target.is_file():
        return "File not found"
    
    return target.read_text(encoding="utf-8")

@tool
def write_file(path: str, content: str) -> str:
    """Create or update a text file in the workspace."""

    target = safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    return f"Successfully wrote: {path}"

@tool
def run_pytest() -> str:
    """Run pytest against the workspace."""

    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "-q"],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )
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
