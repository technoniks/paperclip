from typing import Any, Literal

from pydantic import BaseModel


class AgentResponse(BaseModel):
    status: Literal["success", "partial", "failed"]
    summary: str
    data: dict[str, Any]
    artifacts: list[str]
    issues: list[str]
